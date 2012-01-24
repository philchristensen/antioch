from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import redirect_to

urlpatterns = patterns('antioch.modules.editors.views',
	url(r'^object/', 'object_editor', name='object_editor')
)

