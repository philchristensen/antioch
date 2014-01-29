from django import forms
from django.forms import widgets
from django.forms.models import BaseModelFormSet

import autocomplete_light

from antioch.core import models
from antioch.plugins.editors import tasks

class AuthenticatedModelForm(forms.ModelForm):
	def __init__(self, user_id=None, *args, **kwargs):
		super(AuthenticatedModelForm, self).__init__(*args, **kwargs)
		self.user_id = user_id

class ObjectForm(AuthenticatedModelForm):
	class Meta:
		model = models.Object
		exclude = ('observers',)
	
	owner = forms.ModelChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.ChoiceWidget('ObjectAutocomplete'))
	location = forms.ModelChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.ChoiceWidget('ObjectAutocomplete'), required=False)
	parents = forms.ModelMultipleChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.MultipleChoiceWidget('ObjectAutocomplete'), required=False)
	
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

class PropertyForm(AuthenticatedModelForm):
	class Meta:
		model = models.Property
		exclude = ('origin',)
	
	value = forms.CharField(widget=widgets.HiddenInput)
	owner = forms.ModelChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.ChoiceWidget('ObjectAutocomplete'))
	
	def clean_owner(self):
		value = self.cleaned_data['owner']
		return value.id if value else None
	
	def _post_clean(self):
		pass
	
	def save(self, force_insert=False, force_update=False, commit=True):
		tasks.modifyproperty.delay(
			user_id		= self.user_id,
			object		= self.instance.origin.id,
			property_id	= self.instance.id,
			name		= self.cleaned_data['name'],
			value		= self.cleaned_data['value'],
			type		= self.cleaned_data['type'],
			owner		= self.cleaned_data['owner'],
		).get(timeout=5)
		return self

class VerbForm(AuthenticatedModelForm):
	class Meta:
		model = models.Verb
		exclude = ('origin',)
	
	names = forms.CharField()
	code = forms.CharField(widget=widgets.HiddenInput)
	owner = forms.ModelChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.ChoiceWidget('ObjectAutocomplete'))
	
	def clean_owner(self):
		value = self.cleaned_data['owner']
		return value.id if value else None
	
	def _post_clean(self):
		pass
	
	def save(self, force_insert=False, force_update=False, commit=True):
		tasks.modifyverb.delay(
			user_id		= request.user.avatar.id,
			object		= self.instance.origin.id,
			verb_id		= self.instance.id,
			names		= form.cleaned_data['names'],
			code		= form.cleaned_data['code'],
			ability		= form.cleaned_data['ability'],
			method		= form.cleaned_data['method'],
			owner		= request.POST['owner'],
		).get(timeout=5)
		return self

class AccessForm(forms.ModelForm):
	class Meta:
		model = models.Access
	
	accessor = forms.ModelChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.ChoiceWidget('ObjectAutocomplete'))
	