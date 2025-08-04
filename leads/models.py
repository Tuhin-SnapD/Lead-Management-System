"""
Lead Management System Models

This module contains all the data models for the lead management system,
including User, UserProfile, Lead, Agent, and Category models.
"""

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from typing import Optional
from django.utils import timezone
from simple_history.models import HistoricalRecords
import json


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    Provides additional fields for role-based access control
    and organization management.
    """
    is_organisor = models.BooleanField(
        default=True,
        help_text=_("Designates whether this user is an organizer.")
    )
    is_agent = models.BooleanField(
        default=False,
        help_text=_("Designates whether this user is an agent.")
    )
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=['is_organisor', 'is_agent']),
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]

    def __str__(self) -> str:
        return self.username

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def save(self, *args, **kwargs):
        """Override save to ensure email is lowercase."""
        self.email = self.email.lower()
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """
    UserProfile model for storing additional user information.
    
    Automatically created when a new User is created via signal.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='userprofile'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self) -> str:
        return f"{self.user.username}'s Profile"


class Category(models.Model):
    """
    Category model for organizing leads by status or type.
    
    Examples: New, Contacted, Converted, Unconverted
    """
    name = models.CharField(
        max_length=30,
        help_text=_("Category name (e.g., New, Contacted, Converted)")
    )
    organisation = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE,
        related_name='categories'
    )
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text=_("Hex color code for category display")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        unique_together = ['name', 'organisation']
        indexes = [
            models.Index(fields=['organisation', 'name']),
        ]
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Agent(models.Model):
    """
    Agent model representing sales agents within an organization.
    
    Agents are users who can be assigned leads and manage them.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='agent'
    )
    organisation = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE,
        related_name='agents'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Agent")
        verbose_name_plural = _("Agents")
        indexes = [
            models.Index(fields=['organisation', 'is_active']),
            models.Index(fields=['user']),
        ]

    def __str__(self) -> str:
        return self.user.email

    @property
    def full_name(self) -> str:
        """Return the agent's full name."""
        return self.user.full_name

    @property
    def email(self) -> str:
        """Return the agent's email."""
        return self.user.email


class Lead(models.Model):
    """
    Lead model representing potential customers or sales opportunities.
    
    Leads can be assigned to agents and categorized for better organization.
    """
    # Personal Information
    first_name = models.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]+$',
                message=_("First name can only contain letters and spaces.")
            )
        ]
    )
    last_name = models.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s]+$',
                message=_("Last name can only contain letters and spaces.")
            )
        ]
    )
    age = models.PositiveIntegerField(
        validators=[
            MinValueValidator(0, _("Age cannot be negative.")),
            MaxValueValidator(150, _("Age cannot exceed 150."))
        ],
        help_text=_("Age of the lead")
    )
    
    # Contact Information
    email = models.EmailField(
        unique=True,
        help_text=_("Primary email address")
    )
    phone_number = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
            )
        ],
        help_text=_("Phone number in international format")
    )
    
    # Business Information
    organisation = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE,
        related_name='leads'
    )
    agent = models.ForeignKey(
        Agent, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='assigned_leads'
    )
    category = models.ForeignKey(
        Category, 
        related_name="leads", 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    
    # Additional Information
    description = models.TextField(
        blank=True,
        help_text=_("Additional notes about the lead")
    )
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Source of the lead (e.g., website, referral, cold call)")
    )
    
    # Lead Scoring and ML Features
    lead_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_("Machine learning-based lead score (0-100)")
    )
    engagement_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='low',
        help_text=_("Engagement level based on interactions")
    )
    
    # Follow-up and Reminders
    follow_up_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Scheduled follow-up date")
    )
    follow_up_notes = models.TextField(
        blank=True,
        help_text=_("Notes for the follow-up")
    )
    is_snoozed = models.BooleanField(
        default=False,
        help_text=_("Whether the lead is currently snoozed")
    )
    snooze_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Date until which the lead is snoozed")
    )
    
    # Interaction History
    interaction_count = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of interactions with this lead")
    )
    last_interaction_type = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Type of last interaction (call, email, meeting, etc.)")
    )
    
    # Timestamps
    date_added = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_contacted = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_("Date when the lead was last contacted")
    )

    class Meta:
        verbose_name = _("Lead")
        verbose_name_plural = _("Leads")
        indexes = [
            models.Index(fields=['organisation', 'agent']),
            models.Index(fields=['organisation', 'category']),
            models.Index(fields=['date_added']),
            models.Index(fields=['last_contacted']),
            models.Index(fields=['email']),
            models.Index(fields=['lead_score']),
            models.Index(fields=['follow_up_date']),
            models.Index(fields=['is_snoozed']),
        ]
        ordering = ['-date_added']

    # History tracking
    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self) -> str:
        """Return the lead's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_assigned(self) -> bool:
        """Check if the lead is assigned to an agent."""
        return self.agent is not None

    @property
    def is_categorized(self) -> bool:
        """Check if the lead has a category assigned."""
        return self.category is not None

    def assign_agent(self, agent: Agent) -> None:
        """Assign an agent to this lead."""
        self.agent = agent
        self.save(update_fields=['agent', 'updated_at'])

    def update_category(self, category: Category) -> None:
        """Update the category of this lead."""
        self.category = category
        self.save(update_fields=['category', 'updated_at'])

    def mark_contacted(self) -> None:
        """Mark the lead as contacted."""
        self.last_contacted = timezone.now()
        self.save(update_fields=['last_contacted', 'updated_at'])

    def update_lead_score(self, score: float) -> None:
        """Update the lead score."""
        self.lead_score = max(0.0, min(100.0, score))
        self.save(update_fields=['lead_score', 'updated_at'])

    def schedule_follow_up(self, date: timezone.datetime, notes: str = "") -> None:
        """Schedule a follow-up for this lead."""
        self.follow_up_date = date
        self.follow_up_notes = notes
        self.save(update_fields=['follow_up_date', 'follow_up_notes', 'updated_at'])

    def snooze_lead(self, until_date: timezone.datetime) -> None:
        """Snooze the lead until a specific date."""
        self.is_snoozed = True
        self.snooze_until = until_date
        self.save(update_fields=['is_snoozed', 'snooze_until', 'updated_at'])

    def unsnooze_lead(self) -> None:
        """Remove snooze from the lead."""
        self.is_snoozed = False
        self.snooze_until = None
        self.save(update_fields=['is_snoozed', 'snooze_until', 'updated_at'])

    def record_interaction(self, interaction_type: str) -> None:
        """Record an interaction with the lead."""
        self.interaction_count += 1
        self.last_interaction_type = interaction_type
        self.last_contacted = timezone.now()
        self.save(update_fields=['interaction_count', 'last_interaction_type', 'last_contacted', 'updated_at'])

    def get_priority_level(self) -> str:
        """Get the priority level based on lead score."""
        if self.lead_score >= 80:
            return 'high'
        elif self.lead_score >= 50:
            return 'medium'
        else:
            return 'low'

    @property
    def is_overdue_follow_up(self) -> bool:
        """Check if the follow-up is overdue."""
        if self.follow_up_date and self.follow_up_date < timezone.now():
            return True
        return False

    @property
    def is_snooze_expired(self) -> bool:
        """Check if the snooze period has expired."""
        if self.is_snoozed and self.snooze_until and self.snooze_until < timezone.now():
            return True
        return False


class LeadInteraction(models.Model):
    """
    Model to track interactions with leads.
    """
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='lead_interactions'
    )
    interaction_type = models.CharField(
        max_length=50,
        choices=[
            ('call', 'Phone Call'),
            ('email', 'Email'),
            ('meeting', 'Meeting'),
            ('text', 'Text Message'),
            ('social', 'Social Media'),
            ('other', 'Other'),
        ]
    )
    notes = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Duration of interaction in minutes")
    )
    outcome = models.CharField(
        max_length=50,
        choices=[
            ('positive', 'Positive'),
            ('neutral', 'Neutral'),
            ('negative', 'Negative'),
            ('no_response', 'No Response'),
        ],
        default='neutral'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lead', 'created_at']),
            models.Index(fields=['agent', 'created_at']),
            models.Index(fields=['interaction_type']),
        ]

    def __str__(self) -> str:
        return f"{self.lead.full_name} - {self.interaction_type} by {self.agent.full_name}"


class AgentPerformance(models.Model):
    """
    Model to track agent performance metrics.
    """
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        related_name='performance_records'
    )
    date = models.DateField()
    
    # Performance metrics
    leads_assigned = models.PositiveIntegerField(default=0)
    leads_contacted = models.PositiveIntegerField(default=0)
    leads_converted = models.PositiveIntegerField(default=0)
    total_interactions = models.PositiveIntegerField(default=0)
    average_response_time_hours = models.FloatField(default=0.0)
    
    # Calculated fields
    conversion_rate = models.FloatField(default=0.0)
    contact_rate = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['agent', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['agent', 'date']),
            models.Index(fields=['conversion_rate']),
        ]

    def __str__(self) -> str:
        return f"{self.agent.full_name} - {self.date}"

    def calculate_metrics(self) -> None:
        """Calculate performance metrics."""
        if self.leads_assigned > 0:
            self.conversion_rate = (self.leads_converted / self.leads_assigned) * 100
            self.contact_rate = (self.leads_contacted / self.leads_assigned) * 100
        self.save(update_fields=['conversion_rate', 'contact_rate', 'updated_at'])


class LeadSource(models.Model):
    """
    Model to track lead sources and their performance.
    """
    organisation = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='lead_sources'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['organisation', 'name']
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    @property
    def total_leads(self) -> int:
        """Get total leads from this source."""
        return self.organisation.leads.filter(source=self.name).count()

    @property
    def converted_leads(self) -> int:
        """Get converted leads from this source."""
        return self.organisation.leads.filter(
            source=self.name,
            category__name__icontains='converted'
        ).count()

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate for this source."""
        total = self.total_leads
        if total > 0:
            return (self.converted_leads / total) * 100
        return 0.0


class MLTrainingSession(models.Model):
    """Model to track ML model training sessions."""
    organisation = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    training_date = models.DateTimeField(auto_now_add=True)
    accuracy = models.FloatField()
    training_samples = models.IntegerField()
    test_samples = models.IntegerField()
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
    ])
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-training_date']
    
    def __str__(self):
        return f"ML Training - {self.organisation.user.username} - {self.training_date.strftime('%Y-%m-%d %H:%M')}"


# Signal handlers
def post_user_created_signal(sender: type, instance: User, created: bool, **kwargs) -> None:
    """
    Signal handler to create UserProfile when a new User is created.
    
    Args:
        sender: The User model class
        instance: The User instance that was created
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        UserProfile.objects.create(user=instance)


# Connect the signal
post_save.connect(post_user_created_signal, sender=User)