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

class RootResource(wsgi.WSGIResource):
	isLeaf=True
	def __init__(self, msg_service):
		self.msg_service = msg_service
		
		import django.core.handlers.wsgi
		handler = django.core.handlers.wsgi.WSGIHandler()
		wsgi.WSGIResource.__init__(self, reactor, reactor.getThreadPool(), handler)
	
	@defer.inlineCallbacks
	def render(self, request):
		if(request.postpath):
			if(request.postpath[0] == 'rest'):
				rsrc = RESTResource(request.postpath[1:])
				result = yield rsrc.render(request)
				defer.returnValue(result)
			elif(request.postpath[0] == 'comet'):
				queue = self.msg_service.get_queue(self.user_id)
				yield queue.start()
				messages = yield self.queue.get_available()
				rsrc = CometResource(messages)
				result = yield rsrc.render(request)
				yield self.queue.stop()
				defer.returnValue(result)
		defer.returnValue(wsgi.WSGIResource.render(self, request))

class CometResource(resource.Resource):
	def __init__(self, messages):
		self.messages = messages
	
	@defer.inlineCallbacks
	def render_GET(self, request):
		defer.returnValue(simplejson.dumps(self.messages))

class RESTResource(resource.Resource):
	def __init__(self, segments):
		self.segments = segments
	
	@defer.inlineCallbacks
	def render_POST(self, request):
		command_name = translate_path(self.segments[0])
		klass = get_command_class(command_name)
		if(klass is None):
			raise 404
		
		json = request.content.getvalue()
		options = simplejson.loads(json)
		result = yield klass.run(**options)
		defer.returnValue(simplejson.dumps(result))

