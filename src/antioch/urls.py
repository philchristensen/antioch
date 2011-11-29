from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import redirect_to

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	url(r'^assets/(?P<path>.*)$', 'antioch.client.views.serve_static'),
	url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
	url(r'^admin/', include(admin.site.urls)),
	url(r'', include('antioch.client.urls')),
)

