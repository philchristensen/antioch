# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

from django.conf.urls import patterns, url

urlpatterns = patterns('django.contrib.auth.views',
	url(r'^login/$', 'login', {'template_name': 'login.html'}, name='login'),
) + patterns('antioch.client.views',
	url(r'^rest/(.*)$', 'rest', name='rest'),
	url(r'^comet/$', 'comet', name='comet'),
	url(r'^logout/$', 'logout', name='logout'),
	url(r'^$', 'client', name='client'),
)

