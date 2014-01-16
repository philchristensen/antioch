from django import forms
from django.forms import widgets

import autocomplete_light

from antioch.core import models

class ObjectForm(forms.ModelForm):
	class Meta:
		model = models.Object
		exclude = ('observers',)
	
	id = forms.CharField(widget=forms.TextInput(attrs={'disabled':'disabled'}))
	owner = forms.ModelChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.ChoiceWidget('ObjectAutocomplete'))
	location = forms.ModelChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.ChoiceWidget('ObjectAutocomplete'))
	parents = forms.ModelMultipleChoiceField(models.Object.objects.all(),
		widget=autocomplete_light.MultipleChoiceWidget('ObjectAutocomplete'))

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
