from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import redirect_to

urlpatterns = patterns('antioch.modules.editors.views',
	url(r'^object/', 'object_editor', name='object_editor'),
	url(r'^property/', 'property_editor', name='property_editor'),
	url(r'^verb/', 'verb_editor', name='verb_editor'),
	url(r'^access/', 'access_editor', name='access_editor'),
)

