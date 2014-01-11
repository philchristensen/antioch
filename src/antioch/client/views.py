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

from antioch import plugins, assets, celery
from antioch.core import parser, messaging, tasks

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
	# consumer = messaging.get_blocking_consumer()
	# if(consumer is None):
	# 	return http.HttpResponse('["SHUTDOWN"]', content_type="application/json")
	# 
	# consumer.declare_queue(queue_id)
	# messages = consumer.get_messages(queue_id, None, timeout=10)

	with celery.app.default_connection() as conn:
		from kombu import Exchange, Queue
		exchange = Exchange('antioch', type='direct')
		unbound_queue = Queue(queue_id, exchange=exchange, routing_key=queue_id)
		channel = conn.channel()
		queue = unbound_queue(channel)

	messages = [queue.get()]
	log.debug('returning to client: %s' % messages)
	return http.HttpResponse('[%s]' % ','.join(messages), content_type="application/json")

@login_required
@csrf_exempt
def rest(request, command):
	"""
	Query the appserver and wait for a response.
	"""
	kwargs = simplejson.loads(request.read())

	task = getattr(tasks, command)
	result = task.delay(request.user.avatar.id, **kwargs)
	data = result.get(timeout=settings.JOB_TIMEOUT)
	response = simplejson.dumps(data)

	return http.HttpResponse(response, content_type="application/json")

def logout(request):
	"""
	Logout of antioch.
	"""
	auth.logout(request)
	return shortcuts.redirect('client')
