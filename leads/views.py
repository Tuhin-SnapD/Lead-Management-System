"""
Lead Management Views

This module contains all view classes for the lead management system,
including CRUD operations, authentication, and dashboard views.
"""

import logging
from typing import Any, Dict, Optional
from django.core.mail import send_mail
from django.shortcuts import render, reverse, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib import messages
from django.http import HttpResponse
from django.views import generic
from django.db.models import Q, Count
from django.utils import timezone
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
    CustomLoginForm,
    AssignAgentForm, 
    LeadCategoryUpdateForm,
    LeadFilterForm
)
from .services import LeadService, AgentService, CategoryService

logger = logging.getLogger(__name__)


class CustomLoginView(BaseLoginView):
    """Custom login view with improved form and functionality."""
    template_name = "registration/login.html"
    form_class = CustomLoginForm
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        """Return the success URL."""
        return reverse("dashboard")

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            # Set session to expire when browser closes
            self.request.session.set_expiry(0)
        
        messages.success(self.request, _("Welcome back! You have been successfully logged in."))
        return super().form_valid(form)

    def form_invalid(self, form) -> HttpResponse:
        """Handle invalid form submission."""
        messages.error(self.request, _("Invalid username or password. Please try again."))
        return super().form_invalid(form)


class SignupView(generic.CreateView):
    """View for user registration."""
    template_name = "registration/signup.html"
    form_class = CustomUserCreationForm
    success_url = '/login/'

    def get_success_url(self) -> str:
        """Return the success URL."""
        messages.success(self.request, _("Account created successfully! Please log in."))
        return reverse("login")

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        response = super().form_valid(form)
        messages.success(
            self.request, 
            _("Account created successfully! You can now log in with your credentials.")
        )
        return response

    def form_invalid(self, form) -> HttpResponse:
        """Handle invalid form submission."""
        messages.error(self.request, _("Please correct the errors below and try again."))
        return super().form_invalid(form)


class LandingPageView(generic.TemplateView):
    """Landing page view."""
    template_name = "landing.html"


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    """Dashboard view showing key metrics and statistics."""
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for the dashboard."""
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_organisor:
            # Get organization-specific data
            organisation = self.request.user.userprofile
            
            # Lead statistics
            total_leads = Lead.objects.filter(organisation=organisation).count()
            total_in_past30 = Lead.objects.filter(
                organisation=organisation,
                date_added__gte=timezone.now() - timezone.timedelta(days=30)
            ).count()
            converted_in_past30 = Lead.objects.filter(
                organisation=organisation,
                category__name__icontains='converted',
                date_added__gte=timezone.now() - timezone.timedelta(days=30)
            ).count()
            
            context.update({
                'total_lead_count': total_leads,
                'total_in_past30': total_in_past30,
                'converted_in_past30': converted_in_past30,
            })
        else:
            # Agent-specific data
            agent = self.request.user.agent
            if agent:
                total_leads = Lead.objects.filter(agent=agent).count()
                total_in_past30 = Lead.objects.filter(
                    agent=agent,
                    date_added__gte=timezone.now() - timezone.timedelta(days=30)
                ).count()
                converted_in_past30 = Lead.objects.filter(
                    agent=agent,
                    category__name__icontains='converted',
                    date_added__gte=timezone.now() - timezone.timedelta(days=30)
                ).count()
                
                context.update({
                    'total_lead_count': total_leads,
                    'total_in_past30': total_in_past30,
                    'converted_in_past30': converted_in_past30,
                })
        
        return context


class LeadListView(LoginRequiredMixin, generic.ListView):
    """List view for leads with filtering and search capabilities."""
    template_name = "leads/lead_list.html"
    context_object_name = "leads"
    paginate_by = 20

    def get_queryset(self):
        """Get filtered queryset based on user role and filters."""
        if self.request.user.is_organisor:
            queryset = Lead.objects.filter(organisation=self.request.user.userprofile)
        else:
            queryset = Lead.objects.filter(agent=self.request.user.agent)
        
        # Apply filters
        form = LeadFilterForm(self.request.GET, organisation=self.request.user.userprofile)
        if form.is_valid():
            search = form.cleaned_data.get('search')
            agent = form.cleaned_data.get('agent')
            category = form.cleaned_data.get('category')
            status = form.cleaned_data.get('status')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            
            if search:
                queryset = queryset.filter(
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(email__icontains=search) |
                    Q(phone_number__icontains=search)
                )
            
            if agent:
                queryset = queryset.filter(agent=agent)
            
            if category:
                queryset = queryset.filter(category=category)
            
            if status == 'assigned':
                queryset = queryset.filter(agent__isnull=False)
            elif status == 'unassigned':
                queryset = queryset.filter(agent__isnull=True)
            
            if date_from:
                queryset = queryset.filter(date_added__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(date_added__lte=date_to)
        
        return queryset.select_related('agent', 'category').order_by('-date_added')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for the lead list."""
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_organisor:
            context['unassigned_leads'] = Lead.objects.filter(
                organisation=self.request.user.userprofile,
                agent__isnull=True
            ).select_related('agent', 'category')
        
        context['filter_form'] = LeadFilterForm(
            self.request.GET, 
            organisation=self.request.user.userprofile
        )
        
        return context


class LeadDetailView(LoginRequiredMixin, generic.DetailView):
    """Detail view for individual leads."""
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self):
        """Get queryset based on user role."""
        if self.request.user.is_organisor:
            return Lead.objects.filter(organisation=self.request.user.userprofile)
        else:
            return Lead.objects.filter(agent=self.request.user.agent)


class LeadCreateView(OrganisorAndLoginRequiredMixin, generic.CreateView):
    """Create view for new leads."""
    template_name = "leads/lead_create.html"
    form_class = LeadModelForm

    def get_form_kwargs(self) -> Dict[str, Any]:
        """Get form keyword arguments."""
        kwargs = super().get_form_kwargs()
        kwargs['organisation'] = self.request.user.userprofile
        return kwargs

    def get_success_url(self) -> str:
        """Return the success URL."""
        messages.success(self.request, _("Lead created successfully!"))
        return reverse("leads:lead-list")


class LeadUpdateView(LoginRequiredMixin, generic.UpdateView):
    """Update view for existing leads."""
    template_name = "leads/lead_update.html"
    form_class = LeadModelForm

    def get_queryset(self):
        """Get queryset based on user role."""
        if self.request.user.is_organisor:
            return Lead.objects.filter(organisation=self.request.user.userprofile)
        else:
            return Lead.objects.filter(agent=self.request.user.agent)

    def get_form_kwargs(self) -> Dict[str, Any]:
        """Get form keyword arguments."""
        kwargs = super().get_form_kwargs()
        kwargs['organisation'] = self.request.user.userprofile
        return kwargs

    def get_success_url(self) -> str:
        """Return the success URL."""
        messages.success(self.request, _("Lead updated successfully!"))
        return reverse("leads:lead-detail", kwargs={"pk": self.object.pk})


class LeadDeleteView(OrganisorAndLoginRequiredMixin, generic.DeleteView):
    """Delete view for leads."""
    template_name = "leads/lead_delete.html"

    def get_queryset(self):
        """Get queryset for the organization."""
        return Lead.objects.filter(organisation=self.request.user.userprofile)

    def get_success_url(self) -> str:
        """Return the success URL."""
        messages.success(self.request, _("Lead deleted successfully!"))
        return reverse("leads:lead-list")


class AssignAgentView(OrganisorAndLoginRequiredMixin, generic.FormView):
    """View for assigning agents to leads."""
    template_name = "leads/assign_agent.html"
    form_class = AssignAgentForm

    def get_form_kwargs(self) -> Dict[str, Any]:
        """Get form keyword arguments."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data including lead information."""
        context = super().get_context_data(**kwargs)
        
        # Get the lead information
        lead = get_object_or_404(
            Lead, 
            id=self.kwargs["pk"],
            organisation=self.request.user.userprofile
        )
        context['lead'] = lead
        
        # Get available agents for better display
        context['available_agents'] = Agent.objects.filter(
            organisation=self.request.user.userprofile,
            is_active=True
        ).select_related('user').order_by('user__first_name', 'user__last_name')
        
        return context

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        agent = form.cleaned_data["agent"]
        lead = Lead.objects.get(id=self.kwargs["pk"])
        lead.agent = agent
        lead.save()
        messages.success(self.request, _("Agent assigned successfully!"))
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return the success URL."""
        return reverse("leads:lead-list")


class CategoryListView(LoginRequiredMixin, generic.ListView):
    """List view for categories."""
    template_name = "leads/category_list.html"
    context_object_name = "category_list"

    def get_queryset(self):
        """Get categories for the organization."""
        if self.request.user.is_organisor:
            return Category.objects.filter(organisation=self.request.user.userprofile)
        else:
            return Category.objects.filter(organisation=self.request.user.agent.organisation)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for the category list."""
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_organisor:
            organisation = self.request.user.userprofile
        else:
            organisation = self.request.user.agent.organisation
        
        # Calculate statistics
        total_leads = Lead.objects.filter(organisation=organisation).count()
        unassigned_leads = Lead.objects.filter(
            organisation=organisation,
            category__isnull=True
        ).count()
        
        # Add lead count to each category
        for category in context['category_list']:
            category.lead_count = Lead.objects.filter(
                organisation=organisation,
                category=category
            ).count()
        
        context.update({
            'total_leads': total_leads,
            'unassigned_lead_count': unassigned_leads,
            'active_categories': context['category_list'].count(),
        })
        
        return context


class CategoryDetailView(LoginRequiredMixin, generic.DetailView):
    """Detail view for categories."""
    template_name = "leads/category_detail.html"
    context_object_name = "category"

    def get_queryset(self):
        """Get categories for the organization."""
        if self.request.user.is_organisor:
            return Category.objects.filter(organisation=self.request.user.userprofile)
        else:
            return Category.objects.filter(organisation=self.request.user.agent.organisation)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for the category detail."""
        context = super().get_context_data(**kwargs)
        context['leads'] = Lead.objects.filter(
            category=self.object
        ).select_related('agent').order_by('-date_added')
        return context


class LeadCategoryUpdateView(LoginRequiredMixin, generic.UpdateView):
    """Update view for lead categories."""
    template_name = "leads/lead_category_update.html"
    form_class = LeadCategoryUpdateForm

    def get_queryset(self):
        """Get queryset based on user role."""
        if self.request.user.is_organisor:
            return Lead.objects.filter(organisation=self.request.user.userprofile)
        else:
            return Lead.objects.filter(agent=self.request.user.agent)

    def get_success_url(self) -> str:
        """Return the success URL."""
        messages.success(self.request, _("Lead category updated successfully!"))
        return reverse("leads:lead-detail", kwargs={"pk": self.object.pk})


def handle_not_found(request, exception=None):
    """Custom 404 handler."""
    return render(request, '404error.html', status=404)