# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Registration backend for django-registration support.
"""

import hashlib, random, logging

from antioch.core import models, messaging
from antioch.plugins.signup import forms
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
		user_id = messaging.blocking_run('addplayer',
			name	= cleaned_data['character_name'],
			passwd	= cleaned_data['crypt'],
			enabled	= False,
		)
		
		player = models.Player.get(avatar_id=user_id)
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
		result = messaging.blocking_run('enableplayer',
			player_id = player.id,
		)
		
		user_activated.send(self.__class__, player, request)
		return player
	
	def get_form_class(self, request):
		return forms.SignupForm

