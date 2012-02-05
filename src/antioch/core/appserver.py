# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Setup the appserver interface.
"""

import os.path, urllib

from twisted.application import internet
from twisted.web import server

from antioch import conf
from antioch.client import restful

import simplejson

def run(command, **kwargs):
	command_url = os.path.join(conf.get('appserver-url'), 'rest', command)
	f = urllib.urlopen(command_url, simplejson.dumps(kwargs))
	return simplejson.loads(f.read())

class AppServer(internet.TCPServer):
	def __init__(self, msg_service):
		self.root = restful.Resource(msg_service)
		log_path = conf.get('access-log') or None
		self.factory = server.Site(self.root, logPath=log_path)
		internet.TCPServer.__init__(self, conf.get('appserver-port'), self.factory, interface=conf.get('appserver-interface'))

