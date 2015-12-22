from django.conf.urls import patterns

from antioch import plugins

urlpatterns = patterns('',
	*(plugins.urlconfs())
)