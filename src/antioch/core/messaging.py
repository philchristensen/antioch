# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Enable access to the messaging server
"""

import logging, threading, time, atexit, warnings

import pkg_resources as pkg

from twisted.internet import task, protocol, reactor, defer

from antioch import conf
from antioch.util import mnemo, json

log = logging.getLogger(__name__)

_blocking_consumers = dict()
_async_consumer = None

_server_is_shutting_down = False

def blocking_run(command, as_user=None, appserver_queue=None, response_queue=None, **kwargs):
	from django.conf import settings
	appserver_queue = appserver_queue or settings.APPSERVER_QUEUE
	response_queue = response_queue or settings.RESPONSE_QUEUE
	
	correlation_id = getLocalIdent('response')
	
	if(as_user is not None):
		kwargs['user_id'] = as_user
	
	log.debug("sending appserver message [correlation:%s]: %s(%s)" % (correlation_id, command, kwargs))
	consumer = get_blocking_consumer()
	log.debug("declaring response queue %r" % response_queue)
	consumer.declare_queue(response_queue)
	log.debug("sending message to %r: %r" % (appserver_queue, (command, kwargs)))
	consumer.send_message(appserver_queue, dict(
		command			= command,
		kwargs			= kwargs,
		reply_to		= response_queue,
		correlation_id	= correlation_id,
	))
	
	log.debug("waiting for response from %s" % response_queue)
	msg = consumer.get_messages(response_queue, correlation_id)
	while(len(msg) > 1):
		log.warn('discarding queue cruft: %s' % msg.pop(0))
	
	return msg[0]

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

def shutdown_blocking_consumers():
	global _server_is_shutting_down, _blocking_consumers
	_server_is_shutting_down = True
	for ident, consumer in _blocking_consumers.items():
		consumer.disconnect()
	_blocking_consumers = {}

def configure_twisted_shutdown():
	log.debug('Configuring Twisted shutdown')
	reactor.addSystemEventTrigger("before", "shutdown", shutdown_blocking_consumers)

def configure_django_shutdown():
	warnings.warn('Should be configuring Django shutdown')

def get_blocking_consumer():
	if(_server_is_shutting_down):
		return None
	
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
	def __init__(self):
		self.connected = False
		self.connection = None
		self.channel = None
		self.url = None
	
	def connect(self):
		from pika import BlockingConnection, ConnectionParameters, PlainCredentials
		from antioch.core import parser
		self.url = parser.URL(conf.get('queue-url'))
		log.info("[s] connecting to rabbitmq server at %(host)s:%(port)s with %(user)s" % self.url)
		self.connection = BlockingConnection() #ConnectionParameters(
		# 	host            = self.url['host'],
		# 	port            = int(self.url['port']),
		# 	virtual_host    = self.url['path'][1:] or '/', # not sure about this, but it's all that works,
		# 	credentials     = PlainCredentials(self.url['user'], self.url['passwd']),
		# ))
		log.debug("[s] opening channel on %(host)s:%(port)s" % self.url)
		self.channel = self.connection.channel()
		self.channel.confirm_delivery()
		log.debug("[s] declaring exchange %s" % conf.get('appserver-exchange'))
		frame = self.channel.exchange_declare(
			exchange        = conf.get('appserver-exchange'),
			type            = 'direct',
			auto_delete     = True,
			durable         = False,
		)
		self.connected = True
	
	def disconnect(self):
		if(self.connected):
			log.debug("[s] disconnecting from RabbitMQ server on %(host)s:%(port)s" % self.url)
			try:
				self.channel.close()
			except:
				pass
			try:
				self.connection.close()
			except:
				pass
			self.connected = False
	
	def declare_queue(self, queue_id):
		assert self.connected
		log.debug("[s] declaring queue %s" % queue_id)
		self.channel.queue_declare(
			queue           = queue_id,
			auto_delete     = True,
			durable         = False,
			exclusive       = False,
		)
		self.channel.queue_bind(
			queue           = queue_id,
			exchange        = conf.get('appserver-exchange'),
			routing_key     = queue_id,
		)
	
	def get_messages(self, queue_id, correlation_id, timeout=10):
		assert self.connected
		result = []
		
		consumer_tag = None
		self.channel.stopping = False
		
		def on_request(channel, method_frame, header_frame, body):
			if(header_frame.correlation_id == correlation_id):
				log.debug("%s received: %s" % (queue_id, body))
				result.append(body)
				channel.basic_ack(delivery_tag=method_frame.delivery_tag)
				if not(channel.stopping):
					log.debug('stopping %s' % queue_id)
					channel.stopping = True
					channel.stop_consuming(consumer_tag)
		
		def on_timeout():
			log.debug('%s timeout' % queue_id)
			if not(self.channel.stopping):
				self.channel.stopping = True
				log.debug('stopping %s consumer' % queue_id)
				self.channel.stop_consuming(consumer_tag)
		
		timeout_id = self.connection.add_timeout(time.time() + timeout, on_timeout)
		
		consumer_tag = self.channel.basic_consume(on_request, queue=queue_id)
		self.channel.start_consuming()
		log.debug('[s] removing timeout for %s' % queue_id)
		self.connection.remove_timeout(timeout_id)
		log.debug("[s] %s returned to client: %s" % (queue_id, result))
		return result
	
	def send_message(self, routing_key, msg):
		assert self.connected
		from pika import BasicProperties
		log.debug("[s] sending to %s: %s" % (routing_key, msg))
		self.channel.basic_publish(
			exchange        = conf.get('appserver-exchange'),
			routing_key     = routing_key,
			body            = json.dumps(msg),
			properties      = BasicProperties(
				content_type    = "application/json",
				delivery_mode   = 1,
				reply_to        = msg.get('reply_to'),
				correlation_id  = msg.get('correlation_id'),
			)
		)

class AsyncMessageConsumer(object):
	def __init__(self):
		from antioch.core import parser
		self.url = parser.URL(conf.get('queue-url'))
		from twisted.internet.protocol import ClientCreator
		from txamqp import spec, protocol
		from txamqp.client import TwistedDelegate
		self.cc = ClientCreator(reactor, protocol.AMQClient,
			delegate = TwistedDelegate(),
			vhost	 = self.url['path'][1:] or '/', # not sure about this, but it's all that works
			spec	 = spec.loadString(
				pkg.resource_string('antioch', 'static/spec/amqp0-8.xml'), 'amqp0-8.xml'
			),
		)
	
	@defer.inlineCallbacks
	def connect(self):
		log.info("[a] connecting to rabbitmq server at %(host)s:%(port)s" % self.url)
		try:
			self.protocol = yield self.cc.connectTCP(self.url['host'], int(self.url['port']))
		except:
			import traceback
			log.error("Error in connect: %s" % traceback.format_exc())
			raise
		
		log.debug("[a] authenticating to rabbitmq server as %(user)s" % self.url)
		yield self.protocol.authenticate(self.url['user'], self.url['passwd'])
		
		self.channel = yield self.protocol.channel(1)
		yield self.channel.channel_open()
		log.debug("[a] declaring exchange %s" % conf.get('appserver-exchange'))
		yield self.channel.exchange_declare(
			exchange        = conf.get('appserver-exchange'),
			type            = 'direct',
			auto_delete     = True,
			durable         = False,
		)
		log.debug("[a] declaring queue %s" % conf.get('appserver-queue'))
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
		log.debug("[a] queue bound")
	
	@defer.inlineCallbacks
	def start_consuming(self):
		result = yield self.channel.basic_consume(
			queue           = conf.get('appserver-queue'),
			no_ack          = True,
		)
		self.consumer_tag = result[0]
		log.debug("[a] consuming messages for tag %s" % self.consumer_tag)
		self.queue = yield self.protocol.queue(self.consumer_tag)
		log.debug("[a] queue opened for tag %s" % self.consumer_tag)
	
	@defer.inlineCallbacks
	def disconnect(self):
		from txamqp import client
		try:
			log.debug("[a] cancelling consumer %s" % self.consumer_tag)
			yield self.channel.basic_cancel(self.consumer_tag)
			log.debug("[a] closing the channel")
			yield self.channel.channel_close()
		except client.Closed, e:
			log.debug("[a] received client.Closed exception")
			
		log.debug("[a] disconnecting from RabbitMQ server at %(host)s:%(port)s" % self.url)
		if(self.protocol):
			chan0 = yield self.protocol.channel(0)
			try:
				yield chan0.connection_close()
				log.debug('[a] connection closed')
			except Exception, e:
				log.error("[a] received exception %s" % e)
				
			self.protocol = None
	
	@defer.inlineCallbacks
	def get_message(self):
		from txamqp import queue
		log.debug("[a] looking for message")
		try:
			msg = yield self.queue.get()
		except queue.Closed:
			defer.returnValue(None)
		else:
			defer.returnValue(json.loads(msg.content.body))
	
	@defer.inlineCallbacks
	def send_message(self, routing_key, msg):
		from txamqp import content
		log.debug('[a] sending %s to %s' % (msg, routing_key))
		yield self.channel.basic_publish(
			exchange        = conf.get('appserver-exchange'),
			routing_key     = routing_key,
			content         = content.Content(json.dumps(msg), properties={
				'content type'    :'application/json',
				'delivery mode'   : 1,
				'reply to'        : msg.get('reply_to'),
				'correlation id'  : msg.get('correlation_id'),
			}),
		)
