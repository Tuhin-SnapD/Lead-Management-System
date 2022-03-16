from django import forms
from django.contrib.auth.forms import UserCreationForm, UsernameField
from .models import Lead,User

class LeadModelForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = (
            'first_name',
            'last_name',
            'age',
            'email',
            'agent',
            'state',
        )

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username","email")
        field_classes = {'username': UsernameField, 'email':forms.EmailField}
