# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Django URL routes for static assets.
"""

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('antioch.assets.views',
	url(r'(?P<path>.*)$', 'serve_static'),
)

