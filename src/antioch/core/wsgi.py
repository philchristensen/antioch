# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
WSGI handler
"""

import traceback, logging

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

class DebugLoggingWSGIHandler(WSGIHandler):
	def handle_uncaught_exception(self, request, resolver, exc_info):
		"""
		Log exceptions in request handling even if debugging is on.
		"""
		if settings.DEBUG_PROPAGATE_EXCEPTIONS or settings.DEBUG:
			backtrace = traceback.format_exception(*exc_info)
			log = logging.getLogger('django.request')
			log.error('Internal Server Error: %s\n%s' % (request.path, ''.join(backtrace)))
		return WSGIHandler.handle_uncaught_exception(self, request, resolver, exc_info)

def handler(environ, start_response):
	from antioch import conf
	conf.init()
	
	f = DebugLoggingWSGIHandler()
	return f(environ, start_response)
