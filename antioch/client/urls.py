# antioch
# Copyright (c) 1999-2018 Phil Christensen
#
#
# See LICENSE for details

from django.urls import path

from django.contrib.auth.views import LoginView
from .views import rest, comet, logout, client

app_name = "client"
urlpatterns = [
    path(r'login/', LoginView.as_view(template_name='client/login.html'), name="login"),
    path(r'rest/(.*)', rest, name='rest'),
    path(r'comet/', comet, name='comet'),
    path(r'logout/', logout, name='logout'),
    path(r'', client, name='client'),
]