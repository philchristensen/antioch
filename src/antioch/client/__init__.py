# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Setup the web client interface.
"""

import crypt

from django.contrib.auth import backends

from twisted.internet import reactor
from twisted.application import internet
from twisted.python import log
from twisted.web import wsgi, server

from antioch import conf
from antioch.client import models

class DjangoServer(internet.TCPServer):
	"""
	Provides a service that responds to web requests.
	"""
	def __init__(self, msg_service):
		import django.core.handlers.wsgi
		handler = django.core.handlers.wsgi.WSGIHandler()
		self.root = wsgi.WSGIResource(reactor, reactor.getThreadPool(), handler)
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

