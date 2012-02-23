import os.path, threading, time, logging

from django import template, shortcuts, http
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt

import simplejson

from antioch import plugins, messaging
from antioch.core import parser

_msg_service = None
_msg_service_lock = threading.Lock()

log = logging.getLogger(__name__)

def get_msg_service():
	global _msg_service, _msg_service_lock
	if(_msg_service is not None):
		return _msg_service
	with _msg_service_lock:
		url = parser.URL(settings.QUEUE_URL)
		from amqplib import client_0_8 as amqp
		_msg_service = amqp.Connection(
			host         = "%(host)s:%(port)s" % url,
			userid       = url['user'],
			password     = url['passwd'],
			virtual_host = url['path'],
			insist       = False,
		)
		return _msg_service

def call(command, **kwargs):
	responder_id = messaging.getLocalIdent('responses')
	conn = get_msg_service()
	chan = conn.channel()
	chan.queue_declare(
		queue		= 'appserver',
		durable		= False,
		exclusive	= False,
		auto_delete	= False,
	)
	chan.queue_declare(
		queue		= responder_id,
		durable		= False,
		exclusive	= False,
		auto_delete	= True,
	)
	chan.exchange_declare(
		exchange	= "responder",
		type		= "direct",
		durable		= False,
		auto_delete	= False,
	)
	chan.queue_bind(queue=responder_id, exchange="responder", routing_key=responder_id)
	
	from amqplib import client_0_8 as amqp
	msg = amqp.Message(simplejson.dumps({'command':command, 'kwargs':kwargs, 'responder_id':responder_id}))
	log.debug('published message %s via exchange "responder" with key "appserver", responder: %s' % (msg, responder_id))
	chan.basic_publish(msg, exchange="responder", routing_key='appserver')
	msg = None
	log.debug('listening to queue %s for responses' % responder_id)
	while(not msg):
		msg = chan.basic_get(responder_id)
		if not(msg):
			time.sleep(1)
	
	chan.basic_ack(msg.delivery_tag)
	log.debug('returning %s' % msg.body)
	return msg.body

def get_messages(user_id):
	conn = get_msg_service()
	chan = conn.channel()
	chan.queue_declare(
		queue		= "user-%s-queue" % user_id,
		durable		= False,
		exclusive	= False,
		auto_delete	= True,
	)
	chan.exchange_declare(
		exchange	= "user-exchange",
		type		= "direct",
		durable		= False,
		auto_delete	= False,
	)
	chan.queue_bind(queue="user-%s-queue" % user_id, exchange="user-exchange", routing_key="user-%s" % user_id)
	
	timeout = 30
	messages = []
	while(timeout):
		msg = chan.basic_get("user-%s-queue" % user_id)
		if(msg):
			messages.append(simplejson.loads(msg.body))
		elif(not messages):
			time.sleep(1)
			timeout -= 1
		else:
			break
	return messages

@login_required
def client(request):
	return shortcuts.render_to_response('client.html', dict(
		title           = "antioch client",
		scripts         = [p.script_url for p in plugins.iterate() if p and p.script_url],
	), context_instance=template.RequestContext(request))

@login_required
def comet(request):
	messages = get_messages(request.user.avatar.id)
	return http.HttpResponse(simplejson.dumps(messages), content_type="application/json")

@login_required
@csrf_exempt
def rest(request, command):
	data = simplejson.loads(request.read())
	data['user_id'] = request.user.avatar.id
	try:
		response = call(command, **data)
	except Exception, e:
		import traceback; traceback.print_exc()
		log.error(str(e))
	return http.HttpResponse(response, content_type="application/json")

def logout(request):
	auth.logout(request)
	return shortcuts.redirect('client')
