# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Provide a local REST-style interface to the transaction layer.
"""

from twisted.internet import defer
from twisted.web import resource

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

class TransctionInterface(resource.Resource):
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

