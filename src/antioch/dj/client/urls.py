from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
	url(r'login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
) + patterns('antioch.dj.client.views',
	url(r'logout/$', 'logout', name='logout'),
	url(r'', 'client', name='client'),
)