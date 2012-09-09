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

from antioch import plugins, assets
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
		media           = assets.LessMedia(
			less        = dict(
				screen  = ['%sless/client.less' % settings.STATIC_URL],
			),
			js          = [
				"%sjs/client.js" % settings.STATIC_URL,
				"%sjs/relative-date/lib/relative-date.js" % settings.STATIC_URL,
			]
		),
	), context_instance=template.RequestContext(request))

@login_required
def comet(request):
	"""
	Check for messages for this user.
	"""
	queue_id = '-'.join([settings.USER_QUEUE, str(request.user.avatar.id)])
	log.debug("checking for messages for %s" % queue_id)
	consumer = messaging.get_blocking_consumer()
	consumer.declare_queue(queue_id)
	messages = consumer.get_messages(queue_id, None, timeout=10)
	log.debug('returning to client: %s' % messages)
	return http.HttpResponse('[%s]' % ','.join(messages), content_type="application/json")

@login_required
@csrf_exempt
def rest(request, command):
	"""
	Query the appserver and wait for a response.
	"""
	kwargs = simplejson.loads(request.read())
	kwargs['user_id'] = request.user.avatar.id
	
	correlation_id = messaging.getLocalIdent('response')
	
	log.debug("sending appserver message [correlation:%s]: %s(%s)" % (correlation_id, command, kwargs))
	consumer = messaging.get_blocking_consumer()
	consumer.declare_queue(settings.RESPONSE_QUEUE)
	consumer.send_message(settings.APPSERVER_QUEUE, dict(
		command			= command,
		kwargs			= kwargs,
		reply_to		= settings.RESPONSE_QUEUE,
		correlation_id	= correlation_id,
	))
	
	msg = consumer.get_messages(settings.RESPONSE_QUEUE, correlation_id)
	while(len(msg) > 1):
		log.warn('discarding queue cruft: %s' % msg.pop(0))
	
	return http.HttpResponse(msg[0], content_type="application/json")

def logout(request):
	"""
	Logout of antioch.
	"""
	auth.logout(request)
	return shortcuts.redirect('client')
