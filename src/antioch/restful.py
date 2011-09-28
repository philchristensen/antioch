# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Provide a local REST-style interface to the transaction layer.
"""

from twisted.web import resource

import simplejson

class TransctionInterface(resource.Resource):
	def __init__(self, user, segments):
		self.user = user
		self.segments = segments
	
	def render_GET(self, request):
		return """
			<form action="/actions/%(action)s" method="post">
			<input type="submit" />
			</form>
		""" % dict(
			action = '/'.join(self.segments)
		)
	
	def render_POST(self, request):
		f = getattr(self, 'transact_%s' % self.segments[0], None)
		if(f is None):
			return 404
		
		options = simplejson.loads(request.content.getvalue())
		
		return defer.maybeDeferred(f, options)
	
	def transact_parse(self, options):
		print options