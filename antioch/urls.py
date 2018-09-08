# antioch
# Copyright (c) 1999-2018 Phil Christensen
#
#
# See LICENSE for details

"""
Django URL routes.
"""

from django.urls import include, path

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    path(r'', include('antioch.plugins.urls')),
    path(r'admin/', admin.site.urls),
    path(r'', include('antioch.client.urls')),
]