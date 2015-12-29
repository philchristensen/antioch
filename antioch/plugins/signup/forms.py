from django import forms
from django.forms import widgets

from antioch.core import models

class SignupForm(forms.ModelForm):
    character_name = forms.CharField(max_length=255, required=True)
    email = forms.EmailField(max_length=255, required=True)
    passwd = forms.CharField(max_length=255, widget=widgets.PasswordInput, required=True)
    confirm_passwd = forms.CharField(max_length=255, widget=widgets.PasswordInput, required=True)
    
    class Meta:
        model = models.Player
        fields = []
    
    def clean(self):
        d = super(SignupForm, self).clean()
        passwd = d.get('passwd')
        
        if(d.get('passwd') != d.get('confirm_passwd')):
            self._errors["confirm_passwd"] = self.error_class(["Passwords do not match."])
        
        return d