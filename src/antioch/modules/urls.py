from django.conf.urls.defaults import patterns, url

from antioch.modules import discover_urlconfs

urlpatterns = patterns('',
	*(discover_urlconfs())
)