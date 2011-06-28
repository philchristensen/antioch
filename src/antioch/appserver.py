# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

from txjsonrpc.web import jsonrpc

from antioch import conf, transact

class ControlService(internet.TCPServer):
	"""
	Provides a service that responds to web requests.
	"""
	def __init__(self, msg_service, db_url, access_log):
		self.root = ControlResource()
		self.factory = server.Site(self.root, logPath=conf.get('access-log'))
		
		internet.TCPServer.__init__(self, conf.get('control-port'), self.factory, interface='127.0.0.1')

class ControlResource(jsonrpc.JSONRPC):
	def __init__(self):
		jsonrpc.JSONRPC.__init__(self)
		jsonrpc.addIntrospection(self)
	
	def render(self, request):
		return jsonrpc.JSONRPC.render(self, request)
	
	def jsonrpc_parse(self, user_id, command):
		yield transact.Parse.run(user_id=user_id, sentence=command.encode('utf8'))