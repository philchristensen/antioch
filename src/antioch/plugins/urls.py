from django.conf.urls.defaults import patterns

from antioch import plugins

urlpatterns = patterns('',
	*(plugins.urlconfs())
)