# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Django client views.
"""

import os.path, time, logging

from django import template, shortcuts, http
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt

import simplejson

from antioch import plugins
from antioch.core import parser, messaging

log = logging.getLogger(__name__)

@login_required
def client(request):
	"""
	Return the main client window.
	"""
	return shortcuts.render_to_response('client.html', dict(
		title           = "antioch client",
		scripts         = [p.script_url for p in plugins.iterate() if p and p.script_url],
	), context_instance=template.RequestContext(request))

@login_required
def comet(request):
	"""
	Check for messages for this user.
	"""
	log.debug("checking for messages for %s" % request.user.avatar)
	consumer = messaging.get_blocking_consumer()
	messages = consumer.get_messages('%(queuename)s-%(userid)s' % dict(
		queuename	= settings.USER_QUEUE_PREFIX,
		userid		= request.user.avatar.id,
	), timeout=settings.USER_QUEUE_TIMEOUT, decode=False)
	return http.HttpResponse(messages, content_type="application/json")

@login_required
@csrf_exempt
def rest(request, command):
	"""
	Query the appserver and wait for a response.
	"""
	kwargs = simplejson.loads(request.read())
	kwargs['user_id'] = request.user.avatar.id
	
	responder_id = messaging.getLocalIdent('responses')
	
	log.debug("sending appserver message [responder:%s]: %s(%s)" % (responder_id, command, kwargs))
	consumer = messaging.get_blocking_consumer()
	consumer.send_message(settings.APPSERVER_QUEUE, dict(
		command			= command,
		kwargs			= kwargs,
		responder_id	= responder_id
	))
	
	msg = consumer.expect_message(responder_id, timeout=settings.RESPONSE_QUEUE_TIMEOUT, decode=False)
	return http.HttpResponse(msg, content_type="application/json")

def logout(request):
	"""
	Logout of antioch.
	"""
	auth.logout(request)
	return shortcuts.redirect('client')
