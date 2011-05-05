# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Setup the web client interface.
"""

from twisted.application import internet
from twisted.cred import portal, checkers, credentials

from nevow import guard, appserver

from antioch import client, session, auth, conf

class WebService(internet.TCPServer):
	"""
	Provides a service that responds to web requests.
	"""
	def __init__(self, msg_service):
		self.checker = auth.TransactionChecker()
		self.session_store = session.TransactionUserSessionStore(self.checker, conf.get('db-url-default'))
		self.portal = portal.Portal(session.SessionRealm(self.session_store))
		self.portal.registerChecker(session.SessionChecker(self.session_store))
		self.root = client.RootDelegatePage(self.session_store, msg_service, self.portal)
		self.factory = appserver.NevowSite(self.root, logPath=conf.get('access-log'))
		internet.TCPServer.__init__(self, conf.get('web-port'), self.factory)