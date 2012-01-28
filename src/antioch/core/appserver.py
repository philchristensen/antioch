# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Setup the appserver interface.
"""

from twisted.application import internet
from twisted.web import server

from antioch import conf
from antioch.client import restful

class AppServer(internet.TCPServer):
	def __init__(self, msg_service):
		self.root = restful.Resource(msg_service)
		log_path = conf.get('access-log') or None
		self.factory = server.Site(self.root, logPath=log_path)
		internet.TCPServer.__init__(self, conf.get('appserver-port'), self.factory)

