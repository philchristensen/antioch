# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

from django.conf.urls import url

from django.contrib.auth.views import login
from .views import rest, comet, logout, client

urlpatterns = [
	url(r'^login/$', login, {'template_name': 'client/login.html'}, name='login'),
	url(r'^rest/(.*)$', rest, name='rest'),
	url(r'^comet/$', comet, name='comet'),
	url(r'^logout/$', logout, name='logout'),
	url(r'^$', client, name='client'),
]

