# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Setup the web client interface.
"""

import os

from twisted.internet import reactor
from twisted.application import internet
from twisted.cred import portal, checkers, credentials

from antioch import client, session, auth, conf

class NevowService(internet.TCPServer):
	"""
	Provides a service that responds to web requests.
	"""
	def __init__(self, msg_service, db_url, access_log):
		from nevow import guard, appserver
		self.checker = auth.TransactionChecker()
		self.session_store = session.TransactionUserSessionStore(self.checker, db_url)
		self.portal = portal.Portal(session.SessionRealm(self.session_store))
		self.portal.registerChecker(session.SessionChecker(self.session_store))
		self.root = client.RootDelegatePage(self.session_store, msg_service, self.portal)
		self.factory = appserver.NevowSite(self.root, logPath=access_log)
		internet.TCPServer.__init__(self, conf.get('web-port'), self.factory)

class DjangoService(internet.TCPServer):
	"""
	Provides a service that responds to web requests.
	"""
	def __init__(self, msg_service, db_url, access_log):
		os.environ['DJANGO_SETTINGS_MODULE'] = 'antioch.dj.settings'
		
		import django.core.handlers.wsgi
		self.handler = django.core.handlers.wsgi.WSGIHandler()
		from twisted.web import server, wsgi
		self.root = wsgi.WSGIResource(reactor, reactor.getThreadPool(), self.handler)
		self.factory = server.Site(self.root, logPath=conf.get('access-log'))
		
		internet.TCPServer.__init__(self, conf.get('web-port'), self.factory)
