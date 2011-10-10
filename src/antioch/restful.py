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

from antioch import modules

def translate_path(path):
	return ''.join([x.capitalize() for x in path.split('-')])

def get_command_class(class_name):
	for mod in modules.iterate():
		available_commands = mod.get_commands()
		if(class_name in available_commands):
			klass = available_commands[class_name]
			return klass
	return None

def authenticate(request):
	user_id = None
	return user_id

class RootResource(wsgi.WSGIResource):
	isLeaf=True
	def __init__(self, msg_service):
		self.msg_service = msg_service
		
		import django.core.handlers.wsgi
		handler = django.core.handlers.wsgi.WSGIHandler()
		wsgi.WSGIResource.__init__(self, reactor, reactor.getThreadPool(), handler)
	
	def render(self, request):
		if(request.postpath):
			if(request.postpath[0] == 'rest'):
				rsrc = RESTResource(request.postpath[1:])
				return rsrc.render(request)
			elif(request.postpath[0] == 'comet'):
				d = self.get_messages()
				def _finish(messages):
					if(request.finished):
						return
					rsrc = CometResource(messages)
					output = rsrc.render(request)
					request.write(output)
					request.finish()
				d.addCallback(_finish)
				return server.NOT_DONE_YET
		return wsgi.WSGIResource.render(self, request)
	
	@defer.inlineCallbacks
	def get_messages(self):
		user_id = 2
		queue = self.msg_service.get_queue(user_id)
		yield queue.start()
		messages = []
		while(not messages):
			messages = yield queue.get_available()
		yield queue.stop()
		defer.returnValue(messages)

class CometResource(resource.Resource):
	def __init__(self, messages):
		self.messages = messages
	
	def render_GET(self, request):
		request.setHeader('Content-Type', 'application/json')
		return simplejson.dumps(self.messages)

class RESTResource(resource.Resource):
	def __init__(self, segments):
		self.segments = segments
	
	def render_POST(self, request):
		command_name = translate_path(self.segments[0])
		klass = get_command_class(command_name)
		if(klass is None):
			raise 404
		
		json = request.content.getvalue()
		options = simplejson.loads(json)
		d = klass.run(user_id=2, **options)
		
		def _finish(result):
			if(request.finished):
				return
			request.write(simplejson.dumps(result))
			request.finish()
		d.addCallback(_finish)
		return server.NOT_DONE_YET

