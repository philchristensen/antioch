from django import forms
from ajax_select import fields

from antioch.client import models

class ObjectForm(forms.ModelForm):
	class Meta:
		model = models.Object
		exclude = ('observers',)
	
	owner = fields.AutoCompleteSelectField('object')
	location = fields.AutoCompleteSelectField('object', required=False)
	parents = fields.AutoCompleteSelectMultipleField('object')
