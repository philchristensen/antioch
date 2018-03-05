# antioch
# Copyright (c) 1999-2018 Phil Christensen
#
#
# See LICENSE for details

"""
Django URL routes.
"""

from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'', include('antioch.plugins.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'', include('antioch.client.urls')),
    # url(r'^autocomplete/', include('autocomplete_light.urls'))
]