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

# wget --load-cookies=cookies.dat http://localhost:8888/actions/parse -S --post-data="{\"test\":\"test\"}"

# cookies.dat:
# localhost	TRUE	/	FALSE	1333585359	sid	bd5e02cadf1d9bce4c1dc85c0a542887

class TransctionInterface(resource.Resource):
	def __init__(self, user, segments):
		self.user = user
		self.segments = segments
	
	@defer.inlineCallbacks
	def render_POST(self, request):
		f = getattr(self, 'transact_%s' % self.segments[0], None)
		if(f is None):
			raise 404
		
		json = request.content.getvalue()
		options = simplejson.loads(json)
		result = yield defer.maybeDeferred(f, options)
		defer.returnValue(simplejson.dumps(result))
	
	def transact_parse(self, options):
		return {'result':'success'}