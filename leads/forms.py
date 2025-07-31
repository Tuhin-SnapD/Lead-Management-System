"""
Lead Management Forms

This module contains all form classes for the lead management system,
including lead creation, user registration, and agent assignment forms.
"""

from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserCreationForm, UsernameField, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from typing import Any, Dict

from .models import Lead, Agent, Category
from .services import LeadService

User = get_user_model()


class CustomLoginForm(AuthenticationForm):
    """
    Custom login form with improved styling and validation.
    
    This form extends Django's AuthenticationForm to provide better
    user experience and validation for the lead management system.
    """
    
    username = forms.CharField(
        label=_('Username'),
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Enter your username'),
            'autocomplete': 'username'
        })
    )
    
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Enter your password'),
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        }),
        label=_('Remember me')
    )

    def clean(self) -> Dict[str, Any]:
        """Clean and validate the form data."""
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None:
                raise ValidationError(
                    _('Invalid username or password. Please try again.'),
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user: User) -> None:
        """Check if the user is allowed to log in."""
        if not user.is_active:
            raise ValidationError(
                _('This account is inactive. Please contact support.'),
                code='inactive',
            )


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
    
    username = forms.CharField(
        label=_('Username'),
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Choose a username'),
            'autocomplete': 'username'
        }),
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.')
    )
    
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Enter your email address'),
            'autocomplete': 'email'
        }),
        help_text=_('Enter a valid email address.')
    )
    
    first_name = forms.CharField(
        label=_('First Name'),
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Enter your first name'),
            'autocomplete': 'given-name'
        }),
        help_text=_('Enter your first name.')
    )
    
    last_name = forms.CharField(
        label=_('Last Name'),
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Enter your last name'),
            'autocomplete': 'family-name'
        }),
        help_text=_('Enter your last name.')
    )
    
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Create a strong password'),
            'autocomplete': 'new-password'
        }),
        help_text=_('Your password must contain at least 8 characters.')
    )
    
    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Confirm your password'),
            'autocomplete': 'new-password'
        }),
        help_text=_('Enter the same password as before, for verification.')
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        }),
        label=_('I agree to the Terms of Service and Privacy Policy'),
        error_messages={
            'required': _('You must accept the terms and conditions to continue.')
        }
    )
    
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        field_classes = {'username': UsernameField}

    def clean_email(self) -> str:
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with this email already exists.'))
        return email

    def clean_username(self) -> str:
        """Validate username uniqueness and format."""
        username = self.cleaned_data.get('username')
        if username:
            if User.objects.filter(username=username).exists():
                raise ValidationError(_('A user with this username already exists.'))
            if len(username) < 3:
                raise ValidationError(_('Username must be at least 3 characters long.'))
        return username

    def clean_password2(self) -> str:
        """Validate password confirmation."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Passwords don't match."))
        return password2

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
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Choose an agent to assign')
        }),
        help_text=_("Choose an agent to assign to this lead."),
        error_messages={
            'required': _('Please select an agent to assign to this lead.'),
            'invalid_choice': _('Please select a valid agent from the list.')
        }
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
            
            # Customize the choices to show more information
            choices = [('', _('Select an agent'))]
            for agent in self.fields["agent"].queryset:
                choices.append((
                    agent.id, 
                    f"{agent.user.get_full_name()} ({agent.user.email})"
                ))
            self.fields["agent"].choices = choices


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

