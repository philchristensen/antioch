from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('antioch.dj.client.views',
    url(r'^$', 'client', name='client'),
	url(r'^logout$', 'logout', name='logout'),
) + patterns('',
	url(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
)