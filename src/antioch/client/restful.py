# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Provide a local REST-style interface to the transaction layer.
"""

from twisted.internet import defer, reactor
from twisted.web import resource, server, wsgi
import simplejson

def translate_path(path):
	return ''.join([x.capitalize() for x in path.split('-')])

def get_command_class(class_name):
	from antioch import plugins
	for plugin in plugins.iterate():
		available_commands = plugin.get_commands()
		if(class_name in available_commands):
			klass = available_commands[class_name]
			return klass
	return None

class Resource(resource.Resource):
	isLeaf=True
	def __init__(self, msg_service):
		self.msg_service = msg_service
	
	def render_GET(self, request):
		def _disconnect(resultOrFailure):
			request.notified = True
		request.notifyFinish().addBoth(_disconnect)
		
		d = self.get_messages(request.postpath[1])
		def _finish(messages):
			if(getattr(request, 'notified', False)):
				return
			output = simplejson.dumps(messages)
			request.write(output)
			request.finish()
		d.addCallback(_finish)
		request.setHeader('Content-Type', 'application/json')
		return server.NOT_DONE_YET
	
	@defer.inlineCallbacks
	def get_messages(self, user_id):
		queue = self.msg_service.get_queue(user_id)
		yield queue.start()
		messages = yield queue.get_available()
		yield queue.stop()
		defer.returnValue(messages)
	
	def render_POST(self, request):
		def _disconnect(resultOrFailure):
			request.notified = True
		request.notifyFinish().addBoth(_disconnect)
		
		command_name = translate_path(request.postpath[1])
		klass = get_command_class(command_name)
		if(klass is None):
			request.setResponseCode(404)
			return '404 Not Found'
		
		json = request.content.getvalue()
		options = simplejson.loads(json)
		d = klass.run(**options)
		
		def _finish(result):
			if(getattr(request, 'notified', False)):
				return
			request.setHeader('Content-Type', 'application/json')
			request.write(simplejson.dumps(result))
			request.finish()
		d.addCallback(_finish)
		return server.NOT_DONE_YET

