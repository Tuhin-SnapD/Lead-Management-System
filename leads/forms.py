import email
from sre_parse import State
from django import forms
from .models import Agent, Lead

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

    

