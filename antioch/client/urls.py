# antioch
# Copyright (c) 1999-2019 Phil Christensen
#
#
# See LICENSE for details

from django.urls import path

from django.contrib.auth.views import LoginView
from .views import logout, client

app_name = "client"
urlpatterns = [
    path(r'login/', LoginView.as_view(template_name='client/login.html'), name="login"),
    path(r'logout/', logout, name='logout'),
    path(r'', client, name='client'),
]