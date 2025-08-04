"""
Lead Management Services

This module contains business logic services for lead management operations,
including email notifications, data processing, and analytics.
"""

import logging
from typing import List, Optional, Dict, Any
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Lead, Agent, Category, UserProfile

User = get_user_model()
logger = logging.getLogger(__name__)


class LeadService:
    """Service class for lead-related operations."""
    
    @staticmethod
    def create_lead(
        first_name: str,
        last_name: str,
        email: str,
        phone_number: str,
        age: int,
        organisation: UserProfile,
        description: str = "",
        source: str = "",
        agent: Optional[Agent] = None,
        category: Optional[Category] = None
    ) -> Lead:
        """
        Create a new lead with proper validation and notifications.
        
        Args:
            first_name: Lead's first name
            last_name: Lead's last name
            email: Lead's email address
            phone_number: Lead's phone number
            age: Lead's age
            organisation: Organization profile
            description: Additional description
            source: Lead source
            agent: Assigned agent (optional)
            category: Lead category (optional)
            
        Returns:
            Lead: The created lead instance
            
        Raises:
            ValidationError: If lead data is invalid
        """
        try:
            with transaction.atomic():
                lead = Lead.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone_number=phone_number,
                    age=age,
                    organisation=organisation,
                    description=description,
                    source=source,
                    agent=agent,
                    category=category
                )
                
                # Send notification email
                LeadService._send_lead_created_notification(lead)
                
                logger.info(f"Lead created: {lead.full_name} ({lead.email})")
                return lead
                
        except Exception as e:
            logger.error(f"Error creating lead: {str(e)}")
            raise ValidationError(_("Failed to create lead. Please try again."))
    
    @staticmethod
    def assign_agent_to_lead(lead: Lead, agent: Agent) -> bool:
        """
        Assign an agent to a lead.
        
        Args:
            lead: The lead to assign
            agent: The agent to assign
            
        Returns:
            bool: True if assignment was successful
        """
        try:
            if lead.organisation != agent.organisation:
                raise ValidationError(_("Agent and lead must belong to the same organization."))
            
            lead.assign_agent(agent)
            LeadService._send_agent_assignment_notification(lead, agent)
            
            logger.info(f"Agent {agent.full_name} assigned to lead {lead.full_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning agent to lead: {str(e)}")
            return False
    
    @staticmethod
    def update_lead_category(lead: Lead, category: Category) -> bool:
        """
        Update the category of a lead.
        
        Args:
            lead: The lead to update
            category: The new category
            
        Returns:
            bool: True if update was successful
        """
        try:
            if lead.organisation != category.organisation:
                raise ValidationError(_("Category and lead must belong to the same organization."))
            
            lead.update_category(category)
            logger.info(f"Lead {lead.full_name} category updated to {category.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating lead category: {str(e)}")
            return False
    
    @staticmethod
    def mark_lead_contacted(lead: Lead) -> bool:
        """
        Mark a lead as contacted.
        
        Args:
            lead: The lead to mark as contacted
            
        Returns:
            bool: True if update was successful
        """
        try:
            lead.mark_contacted()
            logger.info(f"Lead {lead.full_name} marked as contacted")
            return True
            
        except Exception as e:
            logger.error(f"Error marking lead as contacted: {str(e)}")
            return False
    
    @staticmethod
    def get_organisation_leads(organisation: UserProfile, filters: Optional[Dict[str, Any]] = None) -> List[Lead]:
        """
        Get leads for an organization with optional filtering.
        
        Args:
            organisation: The organization profile
            filters: Optional filters to apply
            
        Returns:
            List[Lead]: List of leads
        """
        queryset = Lead.objects.filter(organisation=organisation)
        
        if filters:
            if filters.get('agent'):
                queryset = queryset.filter(agent=filters['agent'])
            if filters.get('category'):
                queryset = queryset.filter(category=filters['category'])
            if filters.get('is_assigned') is not None:
                if filters['is_assigned']:
                    queryset = queryset.filter(agent__isnull=False)
                else:
                    queryset = queryset.filter(agent__isnull=True)
            if filters.get('date_from'):
                queryset = queryset.filter(date_added__gte=filters['date_from'])
            if filters.get('date_to'):
                queryset = queryset.filter(date_added__lte=filters['date_to'])
        
        return list(queryset.select_related('agent', 'category', 'agent__user'))
    
    @staticmethod
    def get_lead_statistics(organisation: UserProfile) -> Dict[str, Any]:
        """
        Get lead statistics for an organization.
        
        Args:
            organisation: The organization profile
            
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        leads = Lead.objects.filter(organisation=organisation)
        
        return {
            'total_leads': leads.count(),
            'assigned_leads': leads.filter(agent__isnull=False).count(),
            'unassigned_leads': leads.filter(agent__isnull=True).count(),
            'categorized_leads': leads.filter(category__isnull=False).count(),
            'uncategorized_leads': leads.filter(category__isnull=True).count(),
            'leads_this_month': leads.filter(
                date_added__month=timezone.now().month,
                date_added__year=timezone.now().year
            ).count(),
            'leads_this_week': leads.filter(
                date_added__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
        }
    
    @staticmethod
    def _send_lead_created_notification(lead: Lead) -> None:
        """Send notification email when a lead is created."""
        try:
            subject = f"New Lead Created: {lead.full_name}"
            message = f"""
            A new lead has been created:
            
            Name: {lead.full_name}
            Email: {lead.email}
            Phone: {lead.phone_number}
            Age: {lead.age}
            Source: {lead.source or 'Not specified'}
            
            Go to the dashboard to view and manage this lead.
            """
            
            # Send to organization admin
            if hasattr(lead.organisation.user, 'email'):
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[lead.organisation.user.email],
                    fail_silently=True
                )
                
        except Exception as e:
            logger.error(f"Error sending lead creation notification: {str(e)}")
    
    @staticmethod
    def _send_agent_assignment_notification(lead: Lead, agent: Agent) -> None:
        """Send notification email when an agent is assigned to a lead."""
        try:
            subject = f"Lead Assignment: {lead.full_name}"
            message = f"""
            You have been assigned a new lead:
            
            Lead: {lead.full_name}
            Email: {lead.email}
            Phone: {lead.phone_number}
            
            Please contact this lead as soon as possible.
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[agent.email],
                fail_silently=True
            )
            
        except Exception as e:
            logger.error(f"Error sending agent assignment notification: {str(e)}")


class AgentService:
    """Service class for agent-related operations."""
    
    @staticmethod
    def create_agent(
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        organisation: UserProfile
    ) -> Agent:
        """
        Create a new agent with proper setup.
        
        Args:
            email: Agent's email address
            username: Agent's username
            first_name: Agent's first name
            last_name: Agent's last name
            organisation: Organization profile
            
        Returns:
            Agent: The created agent instance
        """
        try:
            with transaction.atomic():
                # Create user account
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_agent=True,
                    is_organisor=False
                )
                
                # Create agent profile
                agent = Agent.objects.create(
                    user=user,
                    organisation=organisation
                )
                
                # Send welcome email
                AgentService._send_agent_welcome_email(agent)
                
                logger.info(f"Agent created: {agent.full_name} ({agent.email})")
                return agent
                
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise ValidationError(_("Failed to create agent. Please try again."))
    
    @staticmethod
    def get_organisation_agents(organisation: UserProfile, active_only: bool = True) -> List[Agent]:
        """
        Get agents for an organization.
        
        Args:
            organisation: The organization profile
            active_only: Whether to return only active agents
            
        Returns:
            List[Agent]: List of agents
        """
        queryset = Agent.objects.filter(organisation=organisation)
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        return list(queryset.select_related('user'))
    
    @staticmethod
    def get_agent_performance(agent: Agent, days: int = 30) -> Dict[str, Any]:
        """
        Get performance statistics for an agent.
        
        Args:
            agent: The agent
            days: Number of days to look back
            
        Returns:
            Dict[str, Any]: Performance statistics
        """
        from_date = timezone.now() - timezone.timedelta(days=days)
        leads = Lead.objects.filter(
            agent=agent,
            date_added__gte=from_date
        )
        
        return {
            'total_leads': leads.count(),
            'assigned_leads': leads.filter(agent__isnull=False).count(),
            'categorized_leads': leads.filter(category__isnull=False).count(),
            'leads_this_week': leads.filter(
                date_added__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
        }
    
    @staticmethod
    def _send_agent_welcome_email(agent: Agent) -> None:
        """Send welcome email to new agent."""
        try:
            subject = "Welcome to the Lead Management System"
            message = f"""
            Welcome {agent.full_name}!
            
            You have been added as an agent to the Lead Management System.
            Please log in to start managing your leads.
            
            Your login credentials:
            Username: {agent.email}
            
            Please contact your administrator to set up your password.
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[agent.email],
                fail_silently=True
            )
            
        except Exception as e:
            logger.error(f"Error sending agent welcome email: {str(e)}")


class CategoryService:
    """Service class for category-related operations."""
    
    @staticmethod
    def create_default_categories(organisation: UserProfile) -> List[Category]:
        """
        Create default categories for a new organization.
        
        Args:
            organisation: The organization profile
            
        Returns:
            List[Category]: List of created categories
        """
        default_categories = [
            {'name': 'New', 'color': '#3B82F6'},
            {'name': 'Contacted', 'color': '#F59E0B'},
            {'name': 'Converted', 'color': '#10B981'},
            {'name': 'Unconverted', 'color': '#EF4444'},
        ]
        
        categories = []
        for cat_data in default_categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                organisation=organisation,
                defaults={'color': cat_data['color']}
            )
            if created:
                categories.append(category)
        
        return categories
    
    @staticmethod
    def get_organisation_categories(organisation: UserProfile) -> List[Category]:
        """
        Get categories for an organization.
        
        Args:
            organisation: The organization profile
            
        Returns:
            List[Category]: List of categories
        """
        return list(Category.objects.filter(organisation=organisation))
    
    @staticmethod
    def get_category_statistics(organisation: UserProfile) -> Dict[str, Any]:
        """
        Get statistics for each category in an organization.
        
        Args:
            organisation: The organization profile
            
        Returns:
            Dict[str, Any]: Category statistics
        """
        categories = Category.objects.filter(organisation=organisation)
        stats = {}
        
        for category in categories:
            lead_count = Lead.objects.filter(
                organisation=organisation,
                category=category
            ).count()
            
            stats[category.name] = {
                'count': lead_count,
                'color': category.color,
                'percentage': 0  # Will be calculated if needed
            }
        
        return stats 