from django.conf.urls import patterns, include, url

import autocomplete_light
autocomplete_light.autodiscover()

urlpatterns = patterns('antioch.plugins.editors.views',
	url(r'^editor/autocomplete/', include('autocomplete_light.urls')),
	url(r'^editor/object/(\d+)', 'object_editor', name='object_editor'),
	url(r'^editor/property/(\d+)', 'property_editor', name='property_editor'),
	url(r'^editor/verb/(\d+)', 'verb_editor', name='verb_editor'),
	url(r'^editor/access/(\w+)/(\d+)', 'access_editor', name='access_editor'),
)