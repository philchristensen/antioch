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
from antioch.plugins.signup import forms, tasks
from antioch.plugins.signup.models import RegisteredPlayer

from registration.backends.default import DefaultBackend
from registration.signals import user_registered, user_activated

log = logging.getLogger(__name__)

def get_activation_key(username):
	salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
	if isinstance(username, unicode):
		username = username.encode('utf-8')
	return hashlib.sha1(salt+username).hexdigest()

class SignupBackend(DefaultBackend):
	def register(self, request, **cleaned_data):
		user_id = tasks.addplayer.delay(
			name	= cleaned_data['character_name'],
			passwd	= cleaned_data['crypt'],
			enabled	= False,
		).get(timeout=5)
		
		player = models.Player.objects.get(avatar_id=user_id)
		activation_key = get_activation_key(cleaned_data['character_name'])
		reg = models.RegisteredPlayer(
			player			= player,
			email			= cleaned_data['email'],
			activation_key	= activation_key,
		)
		reg.save()
		
		user_registered.send(self.__class__, player, request)
		
		return reg
	
	def activate(self, request, activation_key):
		player = models.RegisteredPlayer.objects.get(activation_key=activation_key)
		result = tasks.enableplayer.delay(
			player_id = player.id,
		).get(timeout=5)
		
		user_activated.send(self.__class__, player, request)
		return player
	
	def get_form_class(self, request):
		return forms.SignupForm

