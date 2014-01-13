from django import forms
from django.forms import widgets

from ajax_select import fields

from antioch.core import models

class ObjectForm(forms.ModelForm):
	class Meta:
		model = models.Object
		exclude = ('observers',)
	
	id = forms.CharField(widget=forms.TextInput(attrs={'disabled':'disabled'}))
	owner = fields.AutoCompleteSelectField('object', help_text='')
	location = fields.AutoCompleteSelectField('object', help_text='', required=False)
	parents = fields.AutoCompleteSelectMultipleField('object', help_text='')

class PropertyForm(forms.ModelForm):
	class Meta:
		model = models.Property
		exclude = ('origin',)
	
	value = forms.CharField(widget=widgets.HiddenInput)
	owner = fields.AutoCompleteSelectField('object', help_text='')

class VerbForm(forms.ModelForm):
	class Meta:
		model = models.Verb
		exclude = ('origin',)
	
	names = forms.CharField()
	code = forms.CharField(widget=widgets.HiddenInput)
	owner = fields.AutoCompleteSelectField('object', help_text='')
