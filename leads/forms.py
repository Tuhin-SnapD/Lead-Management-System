"""
Lead Management Forms

This module contains all form classes for the lead management system,
including lead creation, user registration, and agent assignment forms.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from typing import Any, Dict

from .models import Lead, Agent, Category
from .services import LeadService

User = get_user_model()


class LeadModelForm(forms.ModelForm):
    """
    Model form for creating and updating leads.
    
    This form provides comprehensive validation and field organization
    for lead management operations.
    """
    
    class Meta:
        model = Lead
        fields = (
            'first_name',
            'last_name',
            'age',
            'email',
            'phone_number',
            'description',
            'source',
            'agent',
            'category',
        )
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Enter first name'),
                'maxlength': '50'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Enter last name'),
                'maxlength': '50'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0',
                'max': '150',
                'placeholder': _('Enter age')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': _('Enter email address')
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Enter phone number (e.g., +1234567890)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': '4',
                'placeholder': _('Enter additional notes about the lead')
            }),
            'source': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Enter lead source (e.g., website, referral)')
            }),
            'agent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        help_texts = {
            'first_name': _('Enter the lead\'s first name (letters and spaces only)'),
            'last_name': _('Enter the lead\'s last name (letters and spaces only)'),
            'age': _('Enter the lead\'s age (0-150)'),
            'email': _('Enter a valid email address'),
            'phone_number': _('Enter phone number in international format'),
            'description': _('Optional additional information about the lead'),
            'source': _('Where did this lead come from?'),
            'agent': _('Select an agent to assign to this lead'),
            'category': _('Select a category for this lead'),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the form with organization-specific querysets."""
        self.organisation = kwargs.pop('organisation', None)
        super().__init__(*args, **kwargs)
        
        # Filter agent and category choices by organization
        if self.organisation:
            if 'agent' in self.fields:
                self.fields['agent'].queryset = Agent.objects.filter(
                    organisation=self.organisation,
                    is_active=True
                ).select_related('user')
            
            if 'category' in self.fields:
                self.fields['category'].queryset = Category.objects.filter(
                    organisation=self.organisation
                )

    def clean_email(self) -> str:
        """Validate email uniqueness within the organization."""
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists in the organization
            existing_lead = Lead.objects.filter(
                email=email,
                organisation=self.organisation
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_lead.exists():
                raise ValidationError(_('A lead with this email already exists in your organization.'))
        
        return email

    def clean(self) -> Dict[str, Any]:
        """Perform cross-field validation."""
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        
        # Ensure at least one name field is provided
        if not first_name and not last_name:
            raise ValidationError(_('At least first name or last name must be provided.'))
        
        return cleaned_data


class LeadForm(forms.Form):
    """
    Simple form for basic lead information.
    
    This form is used for quick lead creation without all fields.
    """
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter first name')
        })
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter last name')
        })
    )
    age = forms.IntegerField(
        min_value=0,
        max_value=150,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter age')
        })
    )


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user creation form with improved validation and styling.
    
    This form extends Django's UserCreationForm to provide better
    user experience and validation for the lead management system.
    """
    
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter password')
        }),
        help_text=_('Your password must contain at least 8 characters.')
    )
    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Confirm password')
        }),
        help_text=_('Enter the same password as before, for verification.')
    )
    
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        field_classes = {'username': UsernameField}
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Enter username')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': _('Enter email address')
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Enter first name')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Enter last name')
            }),
        }
        help_texts = {
            "username": _("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),
            "email": _("Enter a valid email address."),
            "first_name": _("Enter your first name."),
            "last_name": _("Enter your last name."),
        }

    def clean_email(self) -> str:
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with this email already exists.'))
        return email

    def save(self, commit: bool = True) -> User:
        """Save the user and create default categories."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Create default categories for the new organization
            from .services import CategoryService
            CategoryService.create_default_categories(user.userprofile)
        
        return user


class AssignAgentForm(forms.Form):
    """
    Form for assigning agents to leads.
    
    This form provides a clean interface for assigning agents
    to unassigned leads.
    """
    
    agent = forms.ModelChoiceField(
        queryset=Agent.objects.none(),
        empty_label=_("Select an agent"),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text=_("Choose an agent to assign to this lead.")
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize with organization-specific agent queryset."""
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        
        if request and request.user.is_organisor:
            self.fields["agent"].queryset = Agent.objects.filter(
                organisation=request.user.userprofile,
                is_active=True
            ).select_related('user').order_by('user__first_name', 'user__last_name')


class LeadCategoryUpdateForm(forms.ModelForm):
    """
    Form for updating lead categories.
    
    This form provides a simple interface for updating
    the category of existing leads.
    """
    
    class Meta:
        model = Lead
        fields = ('category',)
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        help_texts = {
            'category': _('Select a category for this lead')
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize with organization-specific category queryset."""
        super().__init__(*args, **kwargs)
        
        # Filter categories by organization
        if self.instance and self.instance.organisation:
            self.fields['category'].queryset = Category.objects.filter(
                organisation=self.instance.organisation
            ).order_by('name')


class LeadFilterForm(forms.Form):
    """
    Form for filtering leads in the list view.
    
    This form provides filtering options for the lead list,
    allowing users to search and filter leads by various criteria.
    """
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': _('Search leads...')
        }),
        help_text=_('Search by name, email, or phone number')
    )
    
    agent = forms.ModelChoiceField(
        queryset=Agent.objects.none(),
        required=False,
        empty_label=_("All Agents"),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        empty_label=_("All Categories"),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', _('All Statuses')),
            ('assigned', _('Assigned')),
            ('unassigned', _('Unassigned')),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'date'
        })
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize with organization-specific querysets."""
        self.organisation = kwargs.pop('organisation', None)
        super().__init__(*args, **kwargs)
        
        if self.organisation:
            self.fields['agent'].queryset = Agent.objects.filter(
                organisation=self.organisation,
                is_active=True
            ).select_related('user')
            
            self.fields['category'].queryset = Category.objects.filter(
                organisation=self.organisation
            )

    def clean(self) -> Dict[str, Any]:
        """Validate date range."""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError(_('Start date must be before end date.'))
        
        return cleaned_data

