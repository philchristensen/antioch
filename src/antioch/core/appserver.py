# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Setup the appserver interface.
"""

import os.path, urllib, logging

from twisted.application import internet
from twisted.python import log as twisted_log
from twisted.web import server

from antioch import conf
from antioch.client import restful

import simplejson

accesslog = logging.getLogger(__name__ + '.access')

def run(command, **kwargs):
	command_url = os.path.join(conf.get('appserver-url'), 'rest', command)
	f = urllib.urlopen(command_url, simplejson.dumps(kwargs))
	return simplejson.loads(f.read())

class AccessLoggingSite(server.Site):
	def _openLogFile(self, path):
		if(isinstance(path, basestring)):
			f = open(path, "a", 1)
			return f
		elif(hasattr(path, 'read')):
			return path
		else:
			raise ValueError("Unexpected logFile argument: %r" % path)

class AccessLogOnnaStick(twisted_log.StdioOnnaStick):
	def write(self, data):
		if isinstance(data, unicode):
			data = data.encode(self.encoding)
		d = (self.buf + data).split('\n')
		self.buf = d[-1]
		messages = d[0:-1]
		for message in messages:
			accesslog.info(message)
	
	def writelines(self, lines):
		for line in lines:
			if isinstance(line, unicode):
				line = line.encode(self.encoding)
			accesslog.info(line)

class AppServer(internet.TCPServer):
	def __init__(self, msg_service):
		self.root = restful.Resource(msg_service)
		log_path = conf.get('access-log') or AccessLogOnnaStick()
		self.factory = AccessLoggingSite(self.root, logPath=log_path)
		internet.TCPServer.__init__(self, conf.get('appserver-port'), self.factory, interface=conf.get('appserver-interface'))

