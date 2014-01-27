from django import forms
from django.forms import widgets

import autocomplete_light

from antioch.core import models
from antioch.plugins.editors import tasks

class ObjectForm(forms.ModelForm):
	class Meta:
		model = models.Object
		exclude = ('observers',)
	
	owner = forms.ModelChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.ChoiceWidget('ObjectAutocomplete'))
	location = forms.ModelChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.ChoiceWidget('ObjectAutocomplete'), required=False)
	parents = forms.ModelMultipleChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.MultipleChoiceWidget('ObjectAutocomplete'), required=False)
	
	def __init__(self, user_id, *args, **kwargs):
		super(ObjectForm, self).__init__(*args, **kwargs)
		self.user_id = user_id
	
	def clean_location(self):
		value = self.cleaned_data['location']
		return value.id if value else None
	
	def clean_owner(self):
		value = self.cleaned_data['owner']
		return value.id if value else None
	
	def clean_parents(self):
		value = self.cleaned_data['parents']
		return [x.id for x in value or []]
	
	def _post_clean(self):
		pass
	
	def save(self, force_insert=False, force_update=False, commit=True):
		tasks.modifyobject.delay(
			user_id		= self.user_id,
			object		= self.instance.id,
			name		= self.cleaned_data['name'],
			location	= self.cleaned_data['location'],
			owner		= self.cleaned_data['owner'],
			parents		= self.cleaned_data['parents']
		).get(timeout=5)
		return self

class PropertyForm(forms.ModelForm):
	class Meta:
		model = models.Property
		exclude = ('origin',)
	
	value = forms.CharField(widget=widgets.HiddenInput)
	owner = forms.ModelChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.ChoiceWidget('ObjectAutocomplete'))

class VerbForm(forms.ModelForm):
	class Meta:
		model = models.Verb
		exclude = ('origin',)
	
	names = forms.CharField()
	code = forms.CharField(widget=widgets.HiddenInput)
	owner = forms.ModelChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.ChoiceWidget('ObjectAutocomplete'))
