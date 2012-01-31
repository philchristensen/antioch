from django import forms
from ajax_select import fields

from antioch.client import models

class ObjectForm(forms.ModelForm):
	class Meta:
		model = models.Object
	
	owner = fields.AutoCompleteSelectField('object')
	location = fields.AutoCompleteSelectField('object')
	parents = fields.AutoCompleteSelectMultipleField('object')
