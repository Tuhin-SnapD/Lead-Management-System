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
from .models import Lead, Agent, Category, LeadInteraction, AgentPerformance, MLTrainingSession
from .forms import (
    LeadForm, 
    LeadModelForm, 
    CustomUserCreationForm, 
    CustomLoginForm,
    AssignAgentForm, 
    LeadCategoryUpdateForm,
    LeadFilterForm,
    LeadInteractionForm,
    FollowUpForm,
    SnoozeForm,
    LeadScoringForm,
    AgentPerformanceFilterForm
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

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        form.instance.organisation = self.request.user.userprofile
        return super().form_valid(form)

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


class LeadInteractionCreateView(LoginRequiredMixin, generic.CreateView):
    """View for creating lead interactions."""
    template_name = "leads/lead_interaction_create.html"
    form_class = LeadInteractionForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data including lead information."""
        context = super().get_context_data(**kwargs)
        lead = get_object_or_404(
            Lead, 
            id=self.kwargs["lead_id"],
            organisation=self.request.user.userprofile
        )
        context['lead'] = lead
        return context

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        lead = get_object_or_404(
            Lead, 
            id=self.kwargs["lead_id"],
            organisation=self.request.user.userprofile
        )
        
        interaction = form.save(commit=False)
        interaction.lead = lead
        interaction.agent = self.request.user.agent
        interaction.save()
        
        # Update lead interaction count and type
        lead.record_interaction(interaction.interaction_type)
        
        messages.success(self.request, _("Interaction recorded successfully!"))
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return the success URL."""
        return reverse("leads:lead-detail", kwargs={"pk": self.kwargs["lead_id"]})


class FollowUpScheduleView(LoginRequiredMixin, generic.FormView):
    """View for scheduling follow-ups."""
    template_name = "leads/follow_up_schedule.html"
    form_class = FollowUpForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data including lead information."""
        context = super().get_context_data(**kwargs)
        lead = get_object_or_404(
            Lead, 
            id=self.kwargs["lead_id"],
            organisation=self.request.user.userprofile
        )
        context['lead'] = lead
        return context

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        lead = get_object_or_404(
            Lead, 
            id=self.kwargs["lead_id"],
            organisation=self.request.user.userprofile
        )
        
        follow_up_date = form.cleaned_data['follow_up_date']
        follow_up_notes = form.cleaned_data['follow_up_notes']
        send_calendar_invite = form.cleaned_data['send_calendar_invite']
        
        # Schedule follow-up
        lead.schedule_follow_up(follow_up_date, follow_up_notes)
        
        # Send calendar invite if requested
        if send_calendar_invite:
            from .tasks import send_calendar_invite_task
            send_calendar_invite_task.delay(
                lead_id=lead.id,
                agent_id=self.request.user.agent.id,
                meeting_date=follow_up_date.isoformat(),
                duration_minutes=60
            )
        
        messages.success(self.request, _("Follow-up scheduled successfully!"))
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return the success URL."""
        return reverse("leads:lead-detail", kwargs={"pk": self.kwargs["lead_id"]})


class LeadSnoozeView(LoginRequiredMixin, generic.FormView):
    """View for snoozing leads."""
    template_name = "leads/lead_snooze.html"
    form_class = SnoozeForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data including lead information."""
        context = super().get_context_data(**kwargs)
        lead = get_object_or_404(
            Lead, 
            id=self.kwargs["lead_id"],
            organisation=self.request.user.userprofile
        )
        context['lead'] = lead
        return context

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        lead = get_object_or_404(
            Lead, 
            id=self.kwargs["lead_id"],
            organisation=self.request.user.userprofile
        )
        
        snooze_until = form.cleaned_data['snooze_until']
        lead.snooze_lead(snooze_until)
        
        messages.success(self.request, _("Lead snoozed successfully!"))
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return the success URL."""
        return reverse("leads:lead-detail", kwargs={"pk": self.kwargs["lead_id"]})


class LeadUnSnoozeView(LoginRequiredMixin, generic.View):
    """View for unsnoozing leads."""
    
    def post(self, request, *args, **kwargs):
        """Handle POST request to unsnooze lead."""
        lead = get_object_or_404(
            Lead, 
            id=self.kwargs["lead_id"],
            organisation=self.request.user.userprofile
        )
        
        lead.unsnooze_lead()
        messages.success(self.request, _("Lead unsnoozed successfully!"))
        
        return redirect("leads:lead-detail", pk=lead.id)


class LeadScoringView(LoginRequiredMixin, generic.FormView):
    """View for manual lead scoring."""
    template_name = "leads/lead_scoring.html"
    form_class = LeadScoringForm

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data including lead information."""
        context = super().get_context_data(**kwargs)
        lead = get_object_or_404(
            Lead, 
            id=self.kwargs["lead_id"],
            organisation=self.request.user.userprofile
        )
        context['lead'] = lead
        
        # Get ML predicted score
        from .ml_service import lead_scoring_service
        context['ml_score'] = lead_scoring_service.predict_lead_score(lead)
        
        return context

    def form_valid(self, form) -> HttpResponse:
        """Handle valid form submission."""
        lead = get_object_or_404(
            Lead, 
            id=self.kwargs["lead_id"],
            organisation=self.request.user.userprofile
        )
        
        lead_score = form.cleaned_data['lead_score']
        engagement_level = form.cleaned_data['engagement_level']
        
        lead.update_lead_score(lead_score)
        lead.engagement_level = engagement_level
        lead.save(update_fields=['engagement_level', 'updated_at'])
        
        messages.success(self.request, _("Lead score updated successfully!"))
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return the success URL."""
        return reverse("leads:lead-detail", kwargs={"pk": self.kwargs["lead_id"]})


class KanbanBoardView(LoginRequiredMixin, generic.TemplateView):
    """Kanban board view for drag-and-drop lead management."""
    template_name = "leads/kanban_board.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for the Kanban board."""
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_organisor:
            organisation = self.request.user.userprofile
        else:
            organisation = self.request.user.agent.organisation
        
        # Get categories for columns
        categories = Category.objects.filter(organisation=organisation).order_by('name')
        
        # Get leads for each category
        kanban_data = {}
        for category in categories:
            if self.request.user.is_organisor:
                leads = Lead.objects.filter(
                    organisation=organisation,
                    category=category
                ).select_related('agent', 'category').order_by('-lead_score', '-date_added')
            else:
                leads = Lead.objects.filter(
                    agent=self.request.user.agent,
                    category=category
                ).select_related('agent', 'category').order_by('-lead_score', '-date_added')
            
            kanban_data[category.name] = leads
        
        # Get unassigned leads
        if self.request.user.is_organisor:
            unassigned_leads = Lead.objects.filter(
                organisation=organisation,
                category__isnull=True
            ).select_related('agent', 'category').order_by('-lead_score', '-date_added')
        else:
            unassigned_leads = Lead.objects.filter(
                agent=self.request.user.agent,
                category__isnull=True
            ).select_related('agent', 'category').order_by('-lead_score', '-date_added')
        
        kanban_data['Unassigned'] = unassigned_leads
        
        context.update({
            'kanban_data': kanban_data,
            'categories': categories,
        })
        
        return context


class AgentPerformanceView(LoginRequiredMixin, generic.TemplateView):
    """View for agent performance metrics."""
    template_name = "leads/agent_performance.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for agent performance."""
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_organisor:
            organisation = self.request.user.userprofile
        else:
            organisation = self.request.user.agent.organisation
        
        # Get filter form
        filter_form = AgentPerformanceFilterForm(
            self.request.GET, 
            organisation=organisation
        )
        
        # Get performance data
        performance_data = AgentPerformance.objects.filter(
            agent__organisation=organisation
        ).select_related('agent__user')
        
        # Apply filters
        if filter_form.is_valid():
            agent = filter_form.cleaned_data.get('agent')
            date_from = filter_form.cleaned_data.get('date_from')
            date_to = filter_form.cleaned_data.get('date_to')
            metric = filter_form.cleaned_data.get('metric')
            
            if agent:
                performance_data = performance_data.filter(agent=agent)
            
            if date_from:
                performance_data = performance_data.filter(date__gte=date_from)
            
            if date_to:
                performance_data = performance_data.filter(date__lte=date_to)
            
            if metric:
                performance_data = performance_data.order_by(f'-{metric}')
        
        # Get top performers
        top_performers = performance_data.order_by('-conversion_rate')[:5]
        
        # Get performance trends
        from django.db.models import Avg
        from datetime import timedelta
        
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_performance = performance_data.filter(
            date__gte=thirty_days_ago
        ).aggregate(
            avg_conversion_rate=Avg('conversion_rate'),
            avg_contact_rate=Avg('contact_rate'),
            total_leads_assigned=Avg('leads_assigned'),
            total_leads_converted=Avg('leads_converted'),
        )
        
        context.update({
            'filter_form': filter_form,
            'performance_data': performance_data,
            'top_performers': top_performers,
            'recent_performance': recent_performance,
        })
        
        return context


class SourceHeatmapView(LoginRequiredMixin, generic.TemplateView):
    """View for lead source heatmap visualization."""
    template_name = "leads/source_heatmap.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for source heatmap."""
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_organisor:
            organisation = self.request.user.userprofile
        else:
            organisation = self.request.user.agent.organisation
        
        # Get lead sources and their performance
        from django.db.models import Count, Q
        
        sources_data = Lead.objects.filter(
            organisation=organisation
        ).values('source').annotate(
            total_leads=Count('id'),
            converted_leads=Count('id', filter=Q(category__name__icontains='converted')),
            conversion_rate=Count('id', filter=Q(category__name__icontains='converted')) * 100.0 / Count('id')
        ).order_by('-total_leads')
        
        # Prepare data for Chart.js
        labels = []
        total_leads_data = []
        conversion_rates_data = []
        colors = []
        
        for source in sources_data:
            if source['source']:  # Skip empty sources
                labels.append(source['source'])
                total_leads_data.append(source['total_leads'])
                conversion_rates_data.append(round(source['conversion_rate'], 2))
                
                # Color based on conversion rate
                if source['conversion_rate'] > 20:
                    colors.append('#10B981')  # Green
                elif source['conversion_rate'] > 10:
                    colors.append('#F59E0B')  # Yellow
                else:
                    colors.append('#EF4444')  # Red
        
        context.update({
            'sources_data': sources_data,
            'chart_labels': labels,
            'total_leads_data': total_leads_data,
            'conversion_rates_data': conversion_rates_data,
            'colors': colors,
        })
        
        return context


class MLModelTrainingView(OrganisorAndLoginRequiredMixin, generic.View):
    """View for training ML models."""
    
    def get(self, request, *args, **kwargs):
        """Handle GET request to show ML training form."""
        from .ml_service import lead_scoring_service
        import os
        from django.conf import settings
        
        # Get organization context
        if request.user.is_organisor:
            organisation = request.user.userprofile
        else:
            organisation = request.user.agent.organisation
        
        # Get lead statistics
        total_leads = Lead.objects.filter(organisation=organisation).count()
        
        # Check if model files exist
        model_path = os.path.join(settings.ML_MODEL_PATH, 'lead_scoring_model.pkl')
        model_exists = os.path.exists(model_path)
        
        # Get last training info from database
        last_training_session = MLTrainingSession.objects.filter(
            organisation=organisation,
            status='success'
        ).first()
        
        if last_training_session:
            last_training = last_training_session.training_date.strftime('%Y-%m-%d %H:%M')
            accuracy = f"{last_training_session.accuracy:.1%}"
        else:
            last_training = "Never"
            accuracy = "N/A"
        
        # Get recent training sessions
        recent_sessions = MLTrainingSession.objects.filter(
            organisation=organisation
        )[:5]
        
        context = {
            'title': 'Train ML Model',
            'total_leads': total_leads,
            'model_exists': model_exists,
            'last_training': last_training,
            'accuracy': accuracy,
            'organisation': organisation,
            'recent_sessions': recent_sessions,
        }
        
        return render(request, 'leads/train_ml_model.html', context)
    
    def post(self, request, *args, **kwargs):
        """Handle POST request to train ML model."""
        try:
            # Run training synchronously instead of using Celery
            from .ml_service import lead_scoring_service
            
            organisation_id = request.user.userprofile.id
            results = lead_scoring_service.train_model(organisation_id)
            
            if 'error' in results:
                messages.error(
                    self.request, 
                    f"ML model training failed: {results['error']}"
                )
            else:
                messages.success(
                    self.request, 
                    f"ML model training completed successfully! Accuracy: {results.get('accuracy', 0):.2%}"
                )
            
        except Exception as e:
            messages.error(
                self.request, 
                f"ML model training failed: {str(e)}"
            )
        
        # Redirect back to the train ML model page instead of dashboard
        return redirect("leads:train-ml-model")


class DashboardEnhancedView(LoginRequiredMixin, generic.TemplateView):
    """Enhanced dashboard with ML insights and performance metrics."""
    template_name = "dashboard_enhanced.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for enhanced dashboard."""
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_organisor:
            organisation = self.request.user.userprofile
        else:
            organisation = self.request.user.agent.organisation
        
        # Basic metrics
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
        
        # ML insights
        high_score_leads = Lead.objects.filter(
            organisation=organisation,
            lead_score__gte=80
        ).count()
        
        # Assigned leads metrics
        assigned_leads = Lead.objects.filter(
            organisation=organisation,
            agent__isnull=False
        ).count()
        
        assignment_rate = 0
        if total_leads > 0:
            assignment_rate = round((assigned_leads / total_leads) * 100, 1)
        
        # Converted leads metrics
        converted_leads = Lead.objects.filter(
            organisation=organisation,
            category__name__icontains='converted'
        ).count()
        
        conversion_rate = 0
        if total_leads > 0:
            conversion_rate = round((converted_leads / total_leads) * 100, 1)
        
        # Top performing sources
        from django.db.models import Count, Q
        top_sources_raw = Lead.objects.filter(
            organisation=organisation
        ).values('source').annotate(
            total=Count('id'),
            converted=Count('id', filter=Q(category__name__icontains='converted'))
        ).order_by('-total')[:5]
        
        # Calculate conversion rates
        top_sources = []
        for source in top_sources_raw:
            conversion_rate = 0
            if source['total'] > 0:
                conversion_rate = (source['converted'] / source['total']) * 100
            
            top_sources.append({
                'source': source['source'] or 'Unknown',
                'total': source['total'],
                'converted': source['converted'],
                'conversion_rate': round(conversion_rate, 1)
            })
        
        # Recent interactions
        recent_interactions = LeadInteraction.objects.filter(
            lead__organisation=organisation
        ).select_related('lead', 'agent__user').order_by('-created_at')[:10]
        
        context.update({
            'total_lead_count': total_leads,
            'total_in_past30': total_in_past30,
            'converted_in_past30': converted_in_past30,
            'high_score_leads': high_score_leads,
            'assigned_leads': assigned_leads,
            'assignment_rate': assignment_rate,
            'converted_leads': converted_leads,
            'conversion_rate': conversion_rate,
            'top_sources': top_sources,
            'recent_interactions': recent_interactions,
        })
        
        return context


class FeaturesOverviewView(LoginRequiredMixin, generic.TemplateView):
    """Features overview page showing all available features."""
    template_name = "features_overview.html"