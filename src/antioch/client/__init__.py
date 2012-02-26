# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Setup the web client interface.
"""

import crypt, logging, traceback

from django.core.handlers.wsgi import WSGIHandler

from django.contrib.auth import backends
from django.conf import settings

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
	def __init__(self, port):
		self.root = wsgi.WSGIResource(reactor, reactor.getThreadPool(), DebugLoggingWSGIHandler())
		self.factory = AccessLoggingSite(self.root, logPath=AccessLogOnnaStick('django.request.access'))
		internet.TCPServer.__init__(self, port, self.factory)

class DebugLoggingWSGIHandler(WSGIHandler):
	def handle_uncaught_exception(self, request, resolver, exc_info):
		"""
		Log exceptions in request handling even if debugging is on.
		"""
		if settings.DEBUG_PROPAGATE_EXCEPTIONS or settings.DEBUG:
			backtrace = traceback.format_exception(*exc_info)
			log = logging.getLogger('django.request')
			log.error('Internal Server Error: %s\n%s' % (request.path, ''.join(backtrace)))
		return WSGIHandler.handle_uncaught_exception(self, request, resolver, exc_info)

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
			log.error("Error in authenticate(): %s" % traceback.format_exc())

	def get_user(self, user_id):
		try:
			p = models.Player.objects.get(pk=user_id)
			if(p):
				return p
			return None
		except models.Player.DoesNotExist:
			return None

