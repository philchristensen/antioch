# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Setup the web client interface.
"""

import crypt

from zope.interface import implements

from twisted.application import internet
from twisted.web import server
from twisted.python import log

from django.contrib.auth import backends

from antioch import conf
from antioch.client import restful, models

class DjangoService(internet.TCPServer):
	"""
	Provides a service that responds to web requests.
	"""
	def __init__(self, msg_service, db_url, access_log):
		self.root = restful.RootResource(msg_service)
		log_path = conf.get('access-log') or None
		self.factory = server.Site(self.root, logPath=log_path)
		internet.TCPServer.__init__(self, conf.get('web-port'), self.factory)

class DjangoBackend(backends.ModelBackend):
	"""
	Authenticate against the antioch object database.
	"""
	supports_object_permissions = False
	supports_anonymous_user = True
	supports_inactive_user = False

	def authenticate(self, username=None, password=None, request=None):
		try:
			p = models.Player.objects.filter(
				avatar__name__iexact = username,
			)[:1]
			
			if not(p):
				log.msg("Django auth failed.")
				return None
			
			p = p[0]
			if(p.crypt != crypt.crypt(password, p.crypt[0:2])):
				return None
			return p
		except models.Player.DoesNotExist:
			log.msg("Player auth failed.")
			return None
		except Exception, e:
			import traceback
			e = traceback.format_exc()
			log.msg("Error in authenticate(): %s" % e)

	def get_user(self, user_id):
		try:
			p = models.Player.objects.get(pk=user_id)
			if(p):
				return p
			return None
		except models.Player.DoesNotExist:
			return None

