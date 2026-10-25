from django.utils import timezone
from django import forms
from .models import Proposal

class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ['title', 'proposed_time']
        widgets = {
            'proposed_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    def clean_proposed_time(self):
        proposed_time = self.cleaned_data.get('proposed_time')
        if proposed_time < timezone.now():
            raise forms.ValidationError("Оберіть інший час")
        return proposed_time