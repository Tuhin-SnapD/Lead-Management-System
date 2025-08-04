from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from leads.models import Agent

User = get_user_model()


class AgentModelForm(forms.ModelForm):
    """
    Model form for creating and updating agents.
    
    This form handles both user creation and agent assignment.
    """
    
    class Meta:
        model = Agent
        fields = ('user',)
        widgets = {
            'user': forms.Select(attrs={
                'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            })
        }
    
    # Additional fields for user creation
    email = forms.EmailField(
        label=_('Email'),
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Enter agent email address'),
            'autocomplete': 'email'
        }),
        help_text=_('This will be used as the agent\'s login email.')
    )
    
    username = forms.CharField(
        label=_('Username'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Choose a username'),
            'autocomplete': 'username'
        }),
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.')
    )
    
    first_name = forms.CharField(
        label=_('First Name'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Enter first name'),
            'autocomplete': 'given-name'
        }),
        help_text=_('Enter the agent\'s first name.')
    )
    
    last_name = forms.CharField(
        label=_('Last Name'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            'placeholder': _('Enter last name'),
            'autocomplete': 'family-name'
        }),
        help_text=_('Enter the agent\'s last name.')
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with organization-specific user queryset."""
        super().__init__(*args, **kwargs)
        
        # Hide the user field for create operations
        if not self.instance.pk:
            self.fields['user'].widget = forms.HiddenInput()
            self.fields['user'].required = False
            self.fields['email'].required = True
            self.fields['username'].required = True
            self.fields['first_name'].required = True
            self.fields['last_name'].required = True
        else:
            # For updates, show user field and make additional fields read-only
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['first_name'].widget.attrs['readonly'] = True
            self.fields['last_name'].widget.attrs['readonly'] = True

    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user with this email already exists.'))
        return email

    def clean_username(self):
        """Validate username uniqueness."""
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError(_('A user with this username already exists.'))
        return username