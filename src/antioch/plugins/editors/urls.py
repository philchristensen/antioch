from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import redirect_to

from ajax_select import urls as ajax_select_urls

urlpatterns = patterns('antioch.plugins.editors.views',
	url(r'^object/(\d+)', 'object_editor', name='object_editor'),
	url(r'^property/(\d+)', 'property_editor', name='property_editor'),
	url(r'^verb/(\d+)', 'verb_editor', name='verb_editor'),
	url(r'^access/(\w+)/(\d+)', 'access_editor', name='access_editor'),
) + patterns('',
	url(r'^lookups/', include(ajax_select_urls)),
)
