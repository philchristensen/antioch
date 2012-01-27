from django.conf.urls.defaults import patterns

from antioch import modules

urlpatterns = patterns('',
	*(modules.urlconfs())
)