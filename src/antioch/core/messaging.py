# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Enable access to the messaging server
"""

import logging, threading, time

from twisted.internet import task, protocol, reactor, defer

from antioch import conf
from antioch.util import mnemo, json

log = logging.getLogger(__name__)

_blocking_consumers = dict()
_blocking_sleep_interval = 0.010

_async_consumer = None

def getLocalIdent(prefix):
	import os, threading, socket
	thread_id = threading.currentThread().ident
	short_ip = socket.gethostbyname(socket.gethostname())
	long_ip = long(''.join(["%02X" % long(i) for i in short_ip.split('.')]), 16)
	
	return '%(prefix)s-%(process_id)s-%(thread_id)s-%(ip_address)s' % dict(
		prefix		= prefix,
		process_id	= mnemo.encode(os.getpid()),
		thread_id	= mnemo.encode(abs(thread_id)) if thread_id < 0 else 'local',
		ip_address	= mnemo.encode(long_ip),
	)

def get_blocking_consumer():
	ident = getLocalIdent('consumer')
	if(ident not in _blocking_consumers):
		_blocking_consumers[ident] = BlockingMessageConsumer()
		_blocking_consumers[ident].connect()
	return _blocking_consumers[ident]

@defer.inlineCallbacks
def get_async_consumer():
	global _async_consumer
	if(_async_consumer is None):
		_async_consumer = AsyncMessageConsumer()
		yield _async_consumer.connect()
	defer.returnValue(_async_consumer)

class BlockingMessageConsumer(object):
	def connect(self):
		from pika import BlockingConnection, ConnectionParameters, PlainCredentials
		from antioch.core import parser
		self.url = parser.URL(conf.get('queue-url'))
		log.info("[s] connecting to rabbitmq server at %(host)s:%(port)s with %(user)s" % self.url)
		self.connection = BlockingConnection(ConnectionParameters(
			host            = self.url['host'],
			port            = int(self.url['port']),
			virtual_host    = self.url['path'][1:] or '/', # not sure about this, but it's all that works,
			credentials     = PlainCredentials(self.url['user'], self.url['passwd']),
		))
		self.channel = self.connection.channel()
		log.debug("declaring exchange %s" % conf.get('appserver-exchange'))
		frame = self.channel.exchange_declare(
			exchange        = conf.get('appserver-exchange'),
			type            = 'direct',
			#nowait          = True,
			auto_delete     = False,
			durable         = False,
		)
		self.connected = True
	
	def disconnect(self):
		log.debug("disconnecting from RabbitMQ server on %(host)s:%(port)s" % self.url)
		self.connected = False
		self.channel.close()
		self.connection.close()
	
	def declare_queue(self, queue_id):
		assert self.connected
		log.debug("declaring queue %s" % queue_id)
		self.channel.queue_declare(
			queue           = queue_id,
			auto_delete     = True,
			#nowait          = True,
			durable         = False,
			exclusive       = False,
		)
		self.channel.queue_bind(
			queue           = queue_id,
			exchange        = conf.get('appserver-exchange'),
			routing_key     = queue_id,
			#nowait          = True,
		)
	
	def get_messages(self, queue_id, decode=True, timeout=10):
		assert self.connected
		result = []
		check = True
		start_time = time.time()
		while(True):
			check = self.channel.basic_get(ticket=0, queue=queue_id)
			if(check[0].NAME == 'Basic.GetEmpty'):
				if(result or start_time + timeout < time.time()):
					return result
				time.sleep(_blocking_sleep_interval)
			else:
				log.warn("%s received: %s" % (queue_id, check[2]))
				result.append(self.parse_message(*check, decode=decode))
	
	def parse_message(self, method_frame, header_frame, body, decode=True):
		return json.loads(body) if decode else body
	
	def send_message(self, routing_key, msg):
		assert self.connected
		from pika import BasicProperties
		log.debug("sending to %s: %s" % (routing_key, msg))
		self.channel.basic_publish(
			exchange        = conf.get('appserver-exchange'),
			routing_key     = routing_key,
			body            = json.dumps(msg),
			properties      = BasicProperties(
				content_type    = "application/json",
				delivery_mode   = 1,
			)
		)

class AsyncMessageConsumer(object):
	def __init__(self):
		from antioch.core import parser
		self.url = parser.URL(conf.get('queue-url'))
		log.info("[a] connecting to rabbitmq server at %(host)s:%(port)s with %(user)s" % self.url)
		from pika.adapters.twisted_connection import TwistedProtocolConnection
		from pika import ConnectionParameters, PlainCredentials
		self.cc = protocol.ClientCreator(reactor, TwistedProtocolConnection, ConnectionParameters(
			host            = self.url['host'],
			port            = int(self.url['port']),
			virtual_host    = self.url['path'][1:] or '/', # not sure about this, but it's all that works
			credentials     = PlainCredentials(self.url['user'], self.url['passwd']),
		))
	
	@defer.inlineCallbacks
	def connect(self):
		self.protocol = yield self.cc.connectTCP(self.url['host'], int(self.url['port']))
		try:
			self.connection = yield self.protocol.ready
		except:
			import traceback
			log.error("Error in connect: %s" % traceback.format_exc())
			raise
		
		self.channel = yield self.connection.channel()
		yield self.channel.exchange_declare(
			exchange        = conf.get('appserver-exchange'),
			type            = 'direct',
			auto_delete     = False,
			durable         = False,
		)
		yield self.channel.queue_declare(
			queue           = conf.get('appserver-queue'),
			auto_delete     = True,
			durable         = False,
			exclusive       = False,
		)
		yield self.channel.queue_bind(
			queue           = conf.get('appserver-queue'),
			exchange        = conf.get('appserver-exchange'),
			routing_key     = conf.get('appserver-queue'),
		)
	
	@defer.inlineCallbacks
	def start_consuming(self):
		self.queue, self.consumer_tag = yield self.channel.basic_consume(
			queue           = conf.get('appserver-queue'),
			no_ack          = True,
		)
	
	def disconnect(self):
		yield self.channel.close()
		yield self.connection.close()
	
	@defer.inlineCallbacks
	def get_message(self):
		channel, method_frame, header_frame, body = yield self.queue.get()
		defer.returnValue(json.loads(body))
	
	def send_message(self, routing_key, msg):
		from pika import BasicProperties
		self.channel.basic_publish(
			exchange        = conf.get('appserver-exchange'),
			routing_key     = routing_key,
			body            = json.dumps(msg),
			properties      = BasicProperties(
				content_type    = "application/json",
				delivery_mode   = 1,
			)
		)

###############################################################################################
# 
# self.url = parser.URL(queue_url)
# 
# 	from amqplib import client_0_8 as amqp
# 	msg = amqp.Message(simplejson.dumps())
# 	log.debug('published message %s via exchange "responder" with key "appserver", responder: %s' % (msg, responder_id))
# 	chan.basic_publish(msg, exchange="responder", routing_key='appserver')
# 	msg = None
# 	log.debug('listening to queue %s for responses' % responder_id)
# 	while(not msg):
# 		msg = chan.basic_get(responder_id)
# 		if not(msg):
# 			time.sleep(1)
# 	
# 	chan.basic_ack(msg.delivery_tag)
# 	log.debug('returning %s' % msg.body)
# 	return msg.body
# 
# 
# 
# 	responder_id = messaging.getLocalIdent('responses')
# 	conn = get_msg_service()
# 	chan = conn.channel()
# 	chan.queue_declare(
# 		queue		= 'appserver',
# 		durable		= False,
# 		exclusive	= False,
# 		auto_delete	= False,
# 	)
# 	chan.queue_declare(
# 		queue		= responder_id,
# 		durable		= False,
# 		exclusive	= False,
# 		auto_delete	= True,
# 	)
# 	chan.exchange_declare(
# 		exchange	= "responder",
# 		type		= "direct",
# 		durable		= False,
# 		auto_delete	= False,
# 	)
# 	chan.queue_bind(queue=responder_id, exchange="responder", routing_key=responder_id)
# 
# 
# 
# 
# 
# 
# 
# def get_msg_service():
# 	global _msg_service, _msg_service_lock
# 	if(_msg_service is not None):
# 		return _msg_service
# 	with _msg_service_lock:
# 		url = parser.URL(settings.QUEUE_URL)
# 		from amqplib import client_0_8 as amqp
# 		_msg_service = amqp.Connection(
# 			host         = "%(host)s:%(port)s" % url,
# 			userid       = url['user'],
# 			password     = url['passwd'],
# 			virtual_host = url['path'],
# 			insist       = False,
# 		)
# 		return _msg_service
# 
# 
# def get_messages(user_id):
# 	conn = get_msg_service()
# 	chan = conn.channel()
# 	chan.queue_declare(
# 		queue		= "user-%s-queue" % user_id,
# 		durable		= False,
# 		exclusive	= False,
# 		auto_delete	= True,
# 	)
# 	chan.exchange_declare(
# 		exchange	= "user-exchange",
# 		type		= "direct",
# 		durable		= False,
# 		auto_delete	= False,
# 	)
# 	chan.queue_bind(queue="user-%s-queue" % user_id, exchange="user-exchange", routing_key="user-%s" % user_id)
# 	
# 	timeout = 30
# 	messages = []
# 	while(timeout):
# 		msg = chan.basic_get("user-%s-queue" % user_id)
# 		if(msg):
# 			messages.append(simplejson.loads(msg.body))
# 		elif(not messages):
# 			time.sleep(1)
# 			timeout -= 1
# 		else:
# 			break
# 	return messages
# 
# 
# 
# 
# 
# 
# 		from txamqp import content
# 		c = content.Content(simplejson.dumps(result), properties={'content type':'application/json'})
# 		log.debug('returning response %s to %s' % (c, self.ident))
# 		yield self.chan.basic_publish(exchange="responder", content=c, routing_key=data['responder_id'])
# 
# 
# 
# 
# 		from txamqp.queue import Closed as QueueClosed
# 		try:
# 			log.debug('checking for message with %s' % (self.ident,))
# 			msg = yield self.queue.get()
# 			log.debug('found message with %s: %s' % (self.ident, msg))
# 		except QueueClosed, e:
# 			defer.returnValue(None)
# 		
# 		data = simplejson.loads(msg.content.body)
# 
# 
# 
# 		yield self.msg_service.connect()
# 		
# 		self.chan = yield self.msg_service.open_channel()
# 		yield self.chan.exchange_declare(exchange='responder', type="direct", durable=False, auto_delete=False)
# 		yield self.chan.queue_declare(queue='appserver', durable=False, exclusive=False, auto_delete=False)
# 		yield self.chan.queue_bind(queue='appserver', exchange='responder', routing_key='appserver')
# 		yield self.chan.basic_consume(queue='appserver', consumer_tag=self.ident, no_ack=True)
# 		
# 		self.queue = yield self.msg_service.connection.queue(self.ident)
# 		self.stopped = False
# 		
# 		log.debug('declared exchange "responder" with queue/key "appserver", consumer: %s' % (self.ident,))
