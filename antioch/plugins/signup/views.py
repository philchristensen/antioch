"""
Registration backend for django-registration support.
"""

import hashlib, random, logging

from antioch.core import models
from antioch.plugins.signup import forms, tasks
from antioch.plugins.signup.models import RegisteredPlayer

from registration.signals import user_registered, user_activated

from registration.backends.default.views import ActivationView as BaseActivationView
from registration.backends.default.views import RegistrationView as BaseRegistrationView

log = logging.getLogger(__name__)

def get_activation_key(username):
    salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
    if isinstance(username, unicode):
        username = username.encode('utf-8')
    return hashlib.sha1(salt+username).hexdigest()

class RegistrationView(BaseRegistrationView):
    form_class = forms.SignupForm
    
    def register(self, request, **cleaned_data):
        user_id = tasks.addplayer.delay(
            name    = cleaned_data['character_name'],
            passwd    = cleaned_data['passwd'],
            enabled    = False,
        ).get(timeout=5)
        
        assert user_id is not None, "Didn't get an entity ID back from addplayer"
        
        player = models.Player.objects.get(avatar_id=user_id)
        activation_key = get_activation_key(cleaned_data['character_name'])
        
        # it's a hack, but it works well
        player.__class__ = models.RegisteredPlayer
        player.email = cleaned_data['email']
        player.activation_key = activation_key
        player.save()
        
        user_registered.send(sender=self.__class__, user=player, request=request)
        
        return player

class ActivationView(BaseActivationView):
    def activate(self, request, activation_key):
        player = models.RegisteredPlayer.objects.get(activation_key=activation_key)
        result = tasks.enableplayer.delay(player.id).get(timeout=5)
        
        user_activated.send(sender=self.__class__, user=player, request=request)
        return player

