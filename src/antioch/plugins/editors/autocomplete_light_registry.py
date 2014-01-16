import autocomplete_light
from antioch.core import models

class ObjectAutocomplete(autocomplete_light.AutocompleteModelBase):
	search_fields = ['^name']
	autocomplete_js_attributes={'placeholder': 'Select...'}

	def choices_for_request(self):
		if not self.request.user:
			self.choices = self.choices.filter(private=False)
		return super(ObjectAutocomplete, self).choices_for_request()

autocomplete_light.register(models.Object, ObjectAutocomplete)
