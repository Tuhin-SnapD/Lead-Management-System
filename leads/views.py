"""
Lead Management Views

This module contains all view classes for the lead management system,
including CRUD operations, authentication, and dashboard views.
"""

import logging
from typing import Any, Dict, Optional
from django.core.mail import send_mail
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.views import generic
from django.db.models import Q, Count
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from agents.mixins import (
    OrganisorAndLoginRequiredMixin, 
    AgentAndLoginRequiredMixin,
    OrganisationContextMixin
)
from .models import Lead, Agent, Category
from .forms import (
    LeadForm, 
    LeadModelForm, 
    CustomUserCreationForm, 
    AssignAgentForm, 
    LeadCategoryUpdateForm,
    LeadFilterForm
)
from .services import LeadService, AgentService, CategoryService

logger = logging.getLogger(__name__)


class SignupView(generic.CreateView):
    """View for user registration."""
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm
    success_url = '/login/'

    def get_success_url(self) -> str:
        """Return the success URL."""
        messages.success(self.request, _("Account created successfully! Please log in."))
        return reverse("login")


class LandingPageView(generic.TemplateView):
    """Landing page view."""
    template_name = "landing.html"


class DashboardView(LoginRequiredMixin, OrganisationContextMixin, generic.TemplateView):
    """Dashboard view with lead statistics and overview."""
    template_name = "dashboard.html"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add dashboard statistics to context."""
        context = super().get_context_data(**kwargs)
        organisation = self.get_organisation()
        
        if organisation:
            # Get lead statistics
            context['lead_stats'] = LeadService.get_lead_statistics(organisation)
            
            # Get recent leads
            context['recent_leads'] = Lead.objects.filter(
                organisation=organisation
            ).select_related('agent', 'category')[:5]
            
            # Get category statistics
            context['category_stats'] = CategoryService.get_category_statistics(organisation)
            
            # Get agent performance
            agents = AgentService.get_organisation_agents(organisation)
            context['agent_performance'] = {
                agent: AgentService.get_agent_performance(agent) 
                for agent in agents
            }
        
        return context


class LeadListView(LoginRequiredMixin, OrganisationContextMixin, generic.ListView):
    """List view for leads with filtering and search."""
    template_name = "leads/lead_list.html"
    context_object_name = "leads"
    paginate_by = 20

    def get_queryset(self):
        """Get filtered queryset based on user role and filters."""
        user = self.request.user
        organisation = self.get_organisation()
        
        if not organisation:
            return Lead.objects.none()
        
        # Base queryset
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation=organisation)
        else:
            # Agents can only see their assigned leads
            queryset = Lead.objects.filter(
                organisation=organisation,
                agent__user=user
            )
        
        # Apply filters
        filters = self.get_filters()
        if filters:
            queryset = self.apply_filters(queryset, filters)
        
        return queryset.select_related('agent', 'category', 'agent__user').order_by('-date_added')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        organisation = self.get_organisation()
        
        if user.is_organisor and organisation:
            # Add unassigned leads for organizers
            context["unassigned_leads"] = Lead.objects.filter(
                organisation=organisation,
                agent__isnull=True
            ).count()
        
        # Add filter form
        context['filter_form'] = LeadFilterForm(
            data=self.request.GET,
            organisation=organisation
        )
        
        return context
    
    def get_filters(self) -> Optional[Dict[str, Any]]:
        """Extract filters from request."""
        filters = {}
        
        # Search filter
        search = self.request.GET.get('search')
        if search:
            filters['search'] = search
        
        # Agent filter
        agent_id = self.request.GET.get('agent')
        if agent_id:
            try:
                filters['agent'] = Agent.objects.get(id=agent_id)
            except Agent.DoesNotExist:
                pass
        
        # Category filter
        category_id = self.request.GET.get('category')
        if category_id:
            try:
                filters['category'] = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                pass
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            filters['is_assigned'] = status == 'assigned'
        
        # Date filters
        date_from = self.request.GET.get('date_from')
        if date_from:
            filters['date_from'] = date_from
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            filters['date_to'] = date_to
        
        return filters
    
    def apply_filters(self, queryset, filters: Dict[str, Any]):
        """Apply filters to queryset."""
        if filters.get('search'):
            search_term = filters['search']
            queryset = queryset.filter(
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(phone_number__icontains=search_term)
            )
        
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
        
        return queryset


class LeadDetailView(LoginRequiredMixin, OrganisationContextMixin, generic.DetailView):
    """Detail view for individual leads."""
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        """Get queryset based on user role."""
        user = self.request.user
        organisation = self.get_organisation()
        
        if not organisation:
            return Lead.objects.none()
        
        if user.is_organisor:
            return Lead.objects.filter(organisation=organisation)
        else:
            # Agents can only see their assigned leads
            return Lead.objects.filter(
                organisation=organisation,
                agent__user=user
            )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        lead = self.get_object()
        
        # Add category update form
        context['category_form'] = LeadCategoryUpdateForm(instance=lead)
        
        # Add assign agent form for organizers
        if self.request.user.is_organisor:
            context['assign_form'] = AssignAgentForm(request=self.request)
        
        return context


class LeadCreateView(OrganisorAndLoginRequiredMixin, OrganisationContextMixin, generic.CreateView):
    """Create view for new leads."""
    template_name = "leads/lead_create.html"
    form_class = LeadModelForm

    def get_form_kwargs(self) -> Dict[str, Any]:
        """Add organization to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['organisation'] = self.get_organisation()
        return kwargs

    def get_success_url(self) -> str:
        """Return success URL."""
        messages.success(self.request, _("Lead created successfully!"))
        return reverse("leads:lead-list")

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        try:
            lead = form.save(commit=False)
            lead.organisation = self.get_organisation()
            lead.save()
            
            # Send notification email
            self.send_lead_created_notification(lead)
            
            return super().form_valid(form)
            
        except Exception as e:
            logger.error(f"Error creating lead: {str(e)}")
            messages.error(self.request, _("Failed to create lead. Please try again."))
            return self.form_invalid(form)
    
    def send_lead_created_notification(self, lead: Lead) -> None:
        """Send notification email for new lead."""
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
            organisation_user = lead.organisation.user
            if hasattr(organisation_user, 'email'):
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[organisation_user.email],
                    fail_silently=True
                )
                
        except Exception as e:
            logger.error(f"Error sending lead creation notification: {str(e)}")


class LeadUpdateView(OrganisorAndLoginRequiredMixin, OrganisationContextMixin, generic.UpdateView):
    """Update view for existing leads."""
    template_name = "leads/lead_update.html"
    form_class = LeadModelForm

    def get_queryset(self):
        """Get queryset for organizers."""
        organisation = self.get_organisation()
        return Lead.objects.filter(organisation=organisation)

    def get_form_kwargs(self) -> Dict[str, Any]:
        """Add organization to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['organisation'] = self.get_organisation()
        return kwargs

    def get_success_url(self) -> str:
        """Return success URL."""
        messages.success(self.request, _("Lead updated successfully!"))
        return reverse("leads:lead-list")


class LeadDeleteView(OrganisorAndLoginRequiredMixin, OrganisationContextMixin, generic.DeleteView):
    """Delete view for leads."""
    template_name = "leads/lead_delete.html"

    def get_queryset(self):
        """Get queryset for organizers."""
        organisation = self.get_organisation()
        return Lead.objects.filter(organisation=organisation)

    def get_success_url(self) -> str:
        """Return success URL."""
        messages.success(self.request, _("Lead deleted successfully!"))
        return reverse("leads:lead-list")


class AssignAgentView(OrganisorAndLoginRequiredMixin, OrganisationContextMixin, generic.FormView):
    """View for assigning agents to leads."""
    template_name = "leads/assign_agent.html"
    form_class = AssignAgentForm

    def get_form_kwargs(self) -> Dict[str, Any]:
        """Add request to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs
        
    def get_success_url(self) -> str:
        """Return success URL."""
        messages.success(self.request, _("Agent assigned successfully!"))
        return reverse("leads:lead-list")

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        try:
            agent = form.cleaned_data["agent"]
            lead = get_object_or_404(
                Lead, 
                id=self.kwargs["pk"],
                organisation=self.get_organisation()
            )
            
            # Use service to assign agent
            if LeadService.assign_agent_to_lead(lead, agent):
                return super().form_valid(form)
            else:
                messages.error(self.request, _("Failed to assign agent. Please try again."))
                return self.form_invalid(form)
                
        except Exception as e:
            logger.error(f"Error assigning agent: {str(e)}")
            messages.error(self.request, _("Failed to assign agent. Please try again."))
            return self.form_invalid(form)


class CategoryListView(LoginRequiredMixin, OrganisationContextMixin, generic.ListView):
    """List view for categories."""
    template_name = "leads/category_list.html"
    context_object_name = "category_list"

    def get_queryset(self):
        """Get categories for the organization."""
        organisation = self.get_organisation()
        if organisation:
            return Category.objects.filter(organisation=organisation).annotate(
                lead_count=Count('leads')
            )
        return Category.objects.none()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        organisation = self.get_organisation()
        
        if organisation:
            context["unassigned_lead_count"] = Lead.objects.filter(
                organisation=organisation,
                category__isnull=True
            ).count()
        
        return context


class CategoryDetailView(LoginRequiredMixin, OrganisationContextMixin, generic.DetailView):
    """Detail view for categories."""
    template_name = "leads/category_detail.html"
    context_object_name = "category"

    def get_queryset(self):
        """Get categories for the organization."""
        organisation = self.get_organisation()
        if organisation:
            return Category.objects.filter(organisation=organisation)
        return Category.objects.none()

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add leads in this category to context."""
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        
        # Get leads in this category
        context['leads'] = Lead.objects.filter(
            category=category,
            organisation=self.get_organisation()
        ).select_related('agent', 'agent__user')
        
        return context


class LeadCategoryUpdateView(LoginRequiredMixin, OrganisationContextMixin, generic.UpdateView):
    """View for updating lead categories."""
    template_name = "leads/lead_category_update.html"
    form_class = LeadCategoryUpdateForm

    def get_queryset(self):
        """Get queryset based on user role."""
        user = self.request.user
        organisation = self.get_organisation()
        
        if not organisation:
            return Lead.objects.none()
        
        if user.is_organisor:
            return Lead.objects.filter(organisation=organisation)
        else:
            # Agents can only update their assigned leads
            return Lead.objects.filter(
                organisation=organisation,
                agent__user=user
            )

    def get_success_url(self) -> str:
        """Return success URL."""
        messages.success(self.request, _("Lead category updated successfully!"))
        return reverse("leads:lead-detail", kwargs={"pk": self.get_object().id})


def handle_not_found(request, exception) -> HttpResponse:
    """Custom 404 handler."""
    return render(request, '404error.html', status=404)