from django.conf.urls import patterns, include, url

import autocomplete_light
autocomplete_light.autodiscover()

from antioch.plugins.editors import views, forms

urlpatterns = patterns('antioch.plugins.editors.views',
	url(r'^editor/autocomplete/', include('autocomplete_light.urls')),
	url(r'^editor/object/(\d+)', views.EditorFormView(forms.ObjectForm, 'object-editor.html').as_view(), name='object_editor'),
	url(r'^editor/property/(\d+)', views.EditorFormView(forms.PropertyForm, 'property-editor.html').as_view(), name='property_editor'),
	url(r'^editor/verb/(\d+)', views.EditorFormView(forms.VerbForm, 'verb-editor.html').as_view(), name='verb_editor'),
	url(r'^editor/access/(\w+)/(\d+)', 'access_editor', name='access_editor'),
)