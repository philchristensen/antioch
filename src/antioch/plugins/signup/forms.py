from django import forms
from django.forms import widgets

from antioch.core import models
from antioch.util import hash_password

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
		if(passwd and d.get('passwd') == d.get('confirm_passwd')):
			d['crypt'] = hash_password(passwd)
		
		d.pop('passwd', None)
		d.pop('confirm_passwd', None)
		
		return d