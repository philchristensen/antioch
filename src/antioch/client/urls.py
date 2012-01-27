from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('django.contrib.auth.views',
	url(r'^login/$', 'login', {'template_name': 'login.html'}, name='login'),
) + patterns('antioch.client.views',
	url(r'^logout/$', 'logout', name='logout'),
	url(r'^$', 'client', name='client'),
)

