from django.conf.urls import patterns, include, url

import autocomplete_light
autocomplete_light.autodiscover()

from antioch.plugins.editors import views

urlpatterns = patterns('antioch.plugins.editors.views',
	url(r'^editor/autocomplete/', include('autocomplete_light.urls')),
	url(r'^editor/object/(?P<instance_id>\d+)', views.ObjectEditorFormView.as_view(), name='object_editor'),
	url(r'^editor/property/(?P<instance_id>\d+)', views.PropertyEditorFormView.as_view(), name='property_editor'),
	url(r'^editor/verb/(?P<instance_id>\d+)', views.VerbEditorFormView.as_view(), name='verb_editor'),
	url(r'^editor/access/(\w+)/(\d+)', 'access_editor', name='access_editor'),
)