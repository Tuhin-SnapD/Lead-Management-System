"""
Agent Management Views

This module contains all view classes for agent management operations,
including CRUD operations and agent performance tracking.
"""

import logging
from typing import Any, Dict
from django.core.mail import send_mail
from django.views import generic
from django.shortcuts import reverse
from django.contrib import messages
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from leads.models import Agent
from .forms import AgentModelForm
from .mixins import OrganisorAndLoginRequiredMixin, OrganisationContextMixin
from leads.services import AgentService

logger = logging.getLogger(__name__)


class AgentListView(OrganisorAndLoginRequiredMixin, OrganisationContextMixin, generic.ListView):
    """List view for agents with performance statistics."""
    template_name = "agents/agent_list.html"
    context_object_name = "agents"
    paginate_by = 20

    def get_queryset(self):
        """Get agents for the organization with performance data."""
        organisation = self.get_organisation()
        if organisation:
            return Agent.objects.filter(
                organisation=organisation
            ).select_related('user').order_by('user__first_name', 'user__last_name')
        return Agent.objects.none()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add performance statistics to context."""
        context = super().get_context_data(**kwargs)
        organisation = self.get_organisation()
        
        if organisation:
            agents = list(context['agents'])
            context['agent_performance'] = {
                agent: AgentService.get_agent_performance(agent) 
                for agent in agents
            }
        
        return context


class AgentCreateView(OrganisorAndLoginRequiredMixin, OrganisationContextMixin, generic.CreateView):
    """Create view for new agents."""
    template_name = "agents/agent_create.html"
    form_class = AgentModelForm

    def get_success_url(self) -> str:
        """Return success URL."""
        messages.success(self.request, _("Agent created successfully!"))
        return reverse("agents:agent-list")

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        try:
            # Use service to create agent
            agent = AgentService.create_agent(
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                organisation=self.get_organisation()
            )
            
            # Set the form instance for the view
            self.object = agent
            
            return super().form_valid(form)
            
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            messages.error(self.request, _("Failed to create agent. Please try again."))
            return self.form_invalid(form)


class AgentDetailView(OrganisorAndLoginRequiredMixin, OrganisationContextMixin, generic.DetailView):
    """Detail view for individual agents."""
    template_name = "agents/agent_detail.html"
    context_object_name = "agent"

    def get_queryset(self):
        """Get agents for the organization."""
        organisation = self.get_organisation()
        if organisation:
            return Agent.objects.filter(organisation=organisation).select_related('user')
        return Agent.objects.none()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add performance data to context."""
        context = super().get_context_data(**kwargs)
        agent = self.get_object()
        
        # Add performance statistics
        context['performance'] = AgentService.get_agent_performance(agent)
        
        # Add recent leads
        context['recent_leads'] = agent.assigned_leads.select_related('category')[:10]
        
        return context


class AgentUpdateView(OrganisorAndLoginRequiredMixin, OrganisationContextMixin, generic.UpdateView):
    """Update view for existing agents."""
    template_name = "agents/agent_update.html"
    form_class = AgentModelForm

    def get_queryset(self):
        """Get agents for the organization."""
        organisation = self.get_organisation()
        if organisation:
            return Agent.objects.filter(organisation=organisation).select_related('user')
        return Agent.objects.none()

    def get_success_url(self) -> str:
        """Return success URL."""
        messages.success(self.request, _("Agent updated successfully!"))
        return reverse("agents:agent-list")

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        try:
            response = super().form_valid(form)
            
            # Send notification email if email changed
            if form.has_changed() and 'email' in form.changed_data:
                self.send_email_update_notification(form.instance)
            
            return response
            
        except Exception as e:
            logger.error(f"Error updating agent: {str(e)}")
            messages.error(self.request, _("Failed to update agent. Please try again."))
            return self.form_invalid(form)
    
    def send_email_update_notification(self, agent: Agent) -> None:
        """Send notification email when agent email is updated."""
        try:
            subject = "Your Agent Account Has Been Updated"
            message = f"""
            Hello {agent.full_name},
            
            Your agent account has been updated by an administrator.
            If you have any questions, please contact your administrator.
            
            Best regards,
            Lead Management System
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[agent.email],
                fail_silently=True
            )
            
        except Exception as e:
            logger.error(f"Error sending agent update notification: {str(e)}")


class AgentDeleteView(OrganisorAndLoginRequiredMixin, OrganisationContextMixin, generic.DeleteView):
    """Delete view for agents."""
    template_name = "agents/agent_delete.html"
    context_object_name = "agent"

    def get_queryset(self):
        """Get agents for the organization."""
        organisation = self.get_organisation()
        if organisation:
            return Agent.objects.filter(organisation=organisation).select_related('user')
        return Agent.objects.none()

    def get_success_url(self) -> str:
        """Return success URL."""
        messages.success(self.request, _("Agent deleted successfully!"))
        return reverse("agents:agent-list")

    def delete(self, request, *args, **kwargs) -> HttpResponse:
        """Handle agent deletion with proper cleanup."""
        try:
            agent = self.get_object()
            
            # Check if agent has assigned leads
            if agent.assigned_leads.exists():
                messages.warning(
                    request, 
                    _("This agent has assigned leads. Please reassign them before deleting the agent.")
                )
                return self.get(request, *args, **kwargs)
            
            # Send notification email
            self.send_deletion_notification(agent)
            
            # Delete the agent
            response = super().delete(request, *args, **kwargs)
            
            return response
            
        except Exception as e:
            logger.error(f"Error deleting agent: {str(e)}")
            messages.error(request, _("Failed to delete agent. Please try again."))
            return self.get(request, *args, **kwargs)
    
    def send_deletion_notification(self, agent: Agent) -> None:
        """Send notification email when agent is deleted."""
        try:
            subject = "Your Agent Account Has Been Deleted"
            message = f"""
            Hello {agent.full_name},
            
            Your agent account has been deleted by an administrator.
            If you believe this was done in error, please contact your administrator.
            
            Best regards,
            Lead Management System
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[agent.email],
                fail_silently=True
            )
            
        except Exception as e:
            logger.error(f"Error sending agent deletion notification: {str(e)}")


class AgentPerformanceView(OrganisorAndLoginRequiredMixin, OrganisationContextMixin, generic.TemplateView):
    """View for displaying agent performance analytics."""
    template_name = "agents/agent_performance.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add performance data to context."""
        context = super().get_context_data(**kwargs)
        organisation = self.get_organisation()
        
        if organisation:
            # Get all agents with performance data
            agents = AgentService.get_organisation_agents(organisation)
            
            performance_data = {}
            for agent in agents:
                performance_data[agent] = AgentService.get_agent_performance(agent)
            
            context['agent_performance'] = performance_data
            
            # Calculate organization-wide statistics
            context['org_stats'] = self.calculate_organization_stats(agents)
        
        return context
    
    def calculate_organization_stats(self, agents: list) -> Dict[str, Any]:
        """Calculate organization-wide performance statistics."""
        if not agents:
            return {}
        
        total_leads = sum(
            AgentService.get_agent_performance(agent)['total_leads'] 
            for agent in agents
        )
        
        avg_leads_per_agent = total_leads / len(agents) if agents else 0
        
        return {
            'total_agents': len(agents),
            'total_leads': total_leads,
            'avg_leads_per_agent': round(avg_leads_per_agent, 2),
            'active_agents': len([a for a in agents if a.is_active]),
        }
