from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import redirect_to

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
	url(r'^admin/', include(admin.site.urls)),
) + patterns('django.contrib.auth.views',
	url(r'login/$', 'login', {'template_name': 'login.html'}, name='login'),
) + patterns('antioch.client.views',
	url(r'assets/(?P<path>.*)$', 'serve_static'),
	url(r'logout/$', 'logout', name='logout'),
	url(r'$', 'client', name='client'),
)

