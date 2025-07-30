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
        ]
        ordering = ['-date_added']

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
        from django.utils import timezone
        self.last_contacted = timezone.now()
        self.save(update_fields=['last_contacted', 'updated_at'])


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