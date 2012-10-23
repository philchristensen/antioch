# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Registration backend for django-registration support.
"""

import hashlib, random, logging

from antioch.core import models
from antioch.plugins.registration import forms

from registration.backends.default import DefaultBackend
from registration.models import RegistrationManager as DefaultManager
from registration.models import RegistrationProfile as DefaultProfile
from registration.signals import user_registered, user_activated

log = logging.getLogger(__name__)

def get_activation_key(username):
	salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
	if isinstance(username, unicode):
		username = username.encode('utf-8')
	return hashlib.sha1(salt+username).hexdigest()

class RegistrationBackend(DefaultBackend):
	def register(self, request, **cleaned_data):
		player_class = models.Object.objects.get(name='player class')
		lobby = models.Object.objects.get(name='The Lobby')
		
		avatar = models.Object()
		avatar.name = cleaned_data['character_name']
		avatar.unique_name = True
		avatar.location = lobby
		avatar.owner = avatar
		avatar.save()
		avatar.parents.add(player_class)
		
		player = models.Player()
		player.email = cleaned_data['email']
		player.activation_key = get_activation_key(avatar.name)
		player.crypt = cleaned_data['crypt']
		player.avatar = avatar
		player.save()
		
		user_registered.send(self.__class__, player, request)
		
		return player
	
	def activate(self, request, activation_key):
		player = models.Player.objects.get(activation_key=activation_key)
		user_activated.send(self.__class__, player, request)
		return player
	
	def get_form_class(self, request):
		return forms.RegistrationForm

