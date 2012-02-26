# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Setup the web client interface.
"""

import crypt, logging

from django.contrib.auth import backends

from twisted.internet import reactor
from twisted.application import internet
from twisted.web import wsgi, server

from antioch import conf
from antioch.client import models
from antioch.util.logs import AccessLogOnnaStick, AccessLoggingSite

log = logging.getLogger(__name__)

class DjangoServer(internet.TCPServer):
	"""
	Provides a service that responds to web requests.
	"""
	def __init__(self, port=None):
		import django.core.handlers.wsgi
		handler = django.core.handlers.wsgi.WSGIHandler()
		self.root = wsgi.WSGIResource(reactor, reactor.getThreadPool(), handler)
		log_path = conf.get('access-log') or AccessLogOnnaStick('antioch.client.access')
		self.factory = AccessLoggingSite(self.root, logPath=log_path)
		internet.TCPServer.__init__(self, port or conf.get('web-port'), self.factory)

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
				log.error("Django auth failed.")
				return None
			
			p = p[0]
			if(p.crypt != crypt.crypt(password, p.crypt[0:2])):
				return None
			
			log.info('%s logged in' % p.avatar)
			return p
		except models.Player.DoesNotExist:
			log.error("Player auth failed.")
			return None
		except Exception, e:
			import traceback
			log.error("Error in authenticate(): %s" % traceback.format_exc())

	def get_user(self, user_id):
		try:
			p = models.Player.objects.get(pk=user_id)
			if(p):
				return p
			return None
		except models.Player.DoesNotExist:
			return None

