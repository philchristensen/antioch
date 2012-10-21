# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Registration backend for django-registration support.
"""

from antioch.core import models
from antioch.plugins.registration import forms

from registration.backends.default import DefaultBackend
from registration.signals import user_registered, user_activated

class RegistrationBackend(DefaultBackend):
	def register(self, request, **cleaned_data):
		user = None # TODO
		user_registered.send(self.__class__, user, request)
		return user
	
	def activate(self, request, **params):
		user = None # TODO
		user_activated.send(self.__class__, user, request)
		return user
	
	def get_form_class(self, request):
		return forms.PlayerForm

