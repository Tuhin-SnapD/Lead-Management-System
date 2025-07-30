"""
Custom mixins for access control and permissions.

This module provides mixins for handling authentication and authorization
in the lead management system.
"""

from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.views import View
from typing import Any, Optional
from django.utils.translation import gettext_lazy as _


class OrganisorAndLoginRequiredMixin(AccessMixin):
    """
    Mixin to verify that the current user is authenticated and is an organizer.
    
    This mixin ensures that only authenticated users with organizer privileges
    can access the view. Non-authenticated users are redirected to login,
    and non-organizers are redirected to the lead list.
    """
    
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Override dispatch to check authentication and organizer status.
        
        Args:
            request: The HTTP request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: The response object
        """
        if not request.user.is_authenticated:
            messages.error(request, _("You must be logged in to access this page."))
            return self.handle_no_permission()
        
        if not request.user.is_organisor:
            messages.warning(request, _("You don't have permission to access this page."))
            return redirect("leads:lead-list")
        
        return super().dispatch(request, *args, **kwargs)


class AgentAndLoginRequiredMixin(AccessMixin):
    """
    Mixin to verify that the current user is authenticated and is an agent.
    
    This mixin ensures that only authenticated users with agent privileges
    can access the view.
    """
    
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Override dispatch to check authentication and agent status.
        
        Args:
            request: The HTTP request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: The response object
        """
        if not request.user.is_authenticated:
            messages.error(request, _("You must be logged in to access this page."))
            return self.handle_no_permission()
        
        if not request.user.is_agent:
            messages.warning(request, _("You don't have permission to access this page."))
            return redirect("leads:lead-list")
        
        return super().dispatch(request, *args, **kwargs)


class OrganisationContextMixin:
    """
    Mixin to provide organization context to views.
    
    This mixin adds organization-related context data to views
    and provides helper methods for organization-based filtering.
    """
    
    def get_organisation(self) -> Optional['UserProfile']:
        """
        Get the user's organization.
        
        Returns:
            UserProfile: The user's organization profile
        """
        user = self.request.user
        if user.is_organisor:
            return user.userprofile
        elif user.is_agent:
            return user.agent.organisation
        return None
    
    def get_organisation_queryset(self, model_class):
        """
        Get a queryset filtered by the user's organization.
        
        Args:
            model_class: The model class to filter
            
        Returns:
            QuerySet: Filtered queryset
        """
        organisation = self.get_organisation()
        if organisation:
            return model_class.objects.filter(organisation=organisation)
        return model_class.objects.none()
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add organization context to the template context.
        
        Args:
            **kwargs: Additional context data
            
        Returns:
            dict: Updated context data
        """
        context = super().get_context_data(**kwargs)
        context['organisation'] = self.get_organisation()
        return context


class PermissionRequiredMixin(AccessMixin):
    """
    Mixin to check for specific permissions.
    
    This mixin allows views to specify required permissions
    and checks them before allowing access.
    """
    
    permission_required: Optional[str] = None
    
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Override dispatch to check permissions.
        
        Args:
            request: The HTTP request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            HttpResponse: The response object
        """
        if not request.user.is_authenticated:
            messages.error(request, _("You must be logged in to access this page."))
            return self.handle_no_permission()
        
        if self.permission_required and not request.user.has_perm(self.permission_required):
            messages.warning(request, _("You don't have the required permissions."))
            return redirect("leads:lead-list")
        
        return super().dispatch(request, *args, **kwargs)