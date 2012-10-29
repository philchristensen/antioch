from django.db import models

from antioch.core.models import Player

class RegisteredPlayer(Player):
	email = models.CharField(max_length=255)
	activation_key = models.CharField(max_length=255)
