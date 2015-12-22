# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Django view for serving static assets via XSendfile
"""

import os, posixpath, urllib, logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.views import static
from django.contrib.staticfiles import finders

log = logging.getLogger(__name__)

def serve_static(request, path, trailing_slash_handling=False, document_root=None, **kwargs):
	"""
	Serve static files below a given point in the directory structure or
	from locations inferred from the staticfiles finders.

	Instead of raising an error when serving static files in DEBUG mode,
	this view adds an X-Sendfile header.
	"""
	normalized_path = posixpath.normpath(urllib.unquote(path)).lstrip('/')
	if document_root or settings.DEBUG_STATIC:
		absolute_path = os.path.join(document_root or settings.STATIC_ROOT, path)
	else:
		absolute_path = finders.find(normalized_path)

	if not absolute_path:
		raise Http404("'%s' could not be found" % path)
	
	if trailing_slash_handling and not os.path.exists(absolute_path):
		if not(path.endswith('/')):
			try:
				resolve('/%s/' % path)
				return shortcuts.redirect('/%s/' % path, permanent=True)
			except:
				pass
	
	document_root, path = os.path.split(absolute_path)
	if not settings.DEBUG and not settings.XSENDFILE:
		raise ImproperlyConfigured("The staticfiles view can only be used in "
								   "debug mode or when X-Sendfiles is active.")
	
	log.debug("Serving %s from %s with %r" % (path, document_root, kwargs))
	response = static.serve(request, path, document_root=document_root, **kwargs)

	if(settings.XSENDFILE):
		response._container = ['']
		response["X-Sendfile"] = absolute_path
	
	return response
