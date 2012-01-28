from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('antioch.assets.views',
	url(r'(?P<path>.*)$', 'serve_static'),
)

