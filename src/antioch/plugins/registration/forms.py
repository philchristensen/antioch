from django import forms
from django.forms import widgets

from antioch.core import models
from antioch.util import hash_password

class PlayerForm(forms.ModelForm):
	email = forms.EmailField(max_length=255, required=True)
	first_name = forms.CharField(max_length=255, required=True)
	last_name = forms.CharField(max_length=255, required=True)
	passwd = forms.CharField(max_length=255, widget=widgets.PasswordInput, required=True)
	confirm_passwd = forms.CharField(max_length=255, widget=widgets.PasswordInput, required=True)
	
	class Meta:
		model = models.Player
		exclude = ('avatar', 'session_id', 'last_login', 'last_logout', 'wizard', 'crypt')
	
	def clean(self):
		d = super(PlayerForm, self).clean()
		
		passwd = d.get('passwd')
		if(passwd and d.get('passwd') != d.get('confirm_passwd')):
			d['crypt'] = hash_password(passwd)
		
		d.pop('passwd', None)
		d.pop('confirm_passwd', None)
		
		return d