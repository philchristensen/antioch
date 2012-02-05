from django import forms
from django.forms import widgets

from ajax_select import fields

from antioch.client import models

class ObjectForm(forms.ModelForm):
	class Meta:
		model = models.Object
		exclude = ('observers',)
	
	owner = fields.AutoCompleteSelectField('object')
	location = fields.AutoCompleteSelectField('object', required=False)
	parents = fields.AutoCompleteSelectMultipleField('object')

class PropertyForm(forms.ModelForm):
	class Meta:
		model = models.Property
		exclude = ('origin',)
	
	def __init__(self, *args, **kwargs):
		forms.ModelForm.__init__(self, *args, **kwargs)
		self.fields['type'].widget.attrs['class'] = 'ui-widget ui-widget-content'
	
	value = forms.CharField(widget=widgets.HiddenInput)
	owner = fields.AutoCompleteSelectField('object')
