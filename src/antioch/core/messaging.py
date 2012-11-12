# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Enable access to the messaging server
"""

import logging, threading, time

import pkg_resources as pkg

from twisted.internet import task, protocol, reactor, defer

from antioch import conf
from antioch.util import mnemo, json

#import pika.log
#pika.log.setup(level=pika.log.DEBUG)

from pika.callback import CallbackManager

def sanitize(self, key):
	if hasattr(key, 'method') and hasattr(key.method, 'NAME'):
		return key.method.NAME

	if hasattr(key, 'NAME'):
		return key.NAME

	if hasattr(key, '__dict__') and 'NAME' in key.__dict__:
		return key.__dict__['NAME']

	return str(key)

CallbackManager.sanitize = sanitize  # monkey-patch

log = logging.getLogger(__name__)

_blocking_consumers = dict()
_blocking_sleep_interval = 0.010

_async_consumer = None

def blocking_run(command, as_user=None, appserver_queue=None, response_queue=None, **kwargs):
	from django.conf import settings
	appserver_queue = appserver_queue or settings.APPSERVER_QUEUE
	response_queue = response_queue or settings.RESPONSE_QUEUE
	
	correlation_id = getLocalIdent('response')
	
	if(as_user is not None):
		kwargs['user_id'] = as_user
	
	log.debug("sending appserver message [correlation:%s]: %s(%s)" % (correlation_id, command, kwargs))
	consumer = get_blocking_consumer()
	consumer.declare_queue(response_queue)
	consumer.send_message(appserver_queue, dict(
		command			= command,
		kwargs			= kwargs,
		reply_to		= response_queue,
		correlation_id	= correlation_id,
	))
	
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
		self.channel.confirm_delivery(lambda *args, **kwargs: None)
		log.debug("declaring exchange %s" % conf.get('appserver-exchange'))
		frame = self.channel.exchange_declare(
			exchange        = conf.get('appserver-exchange'),
			type            = 'direct',
			auto_delete     = True,
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
		log.debug('removing timeout for %s' % queue_id)
		self.connection.remove_timeout(timeout_id)
		log.debug("%s returned to client: %s" % (queue_id, result))
		return result
	
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
	
	def disconnect(self):
		yield self.channel.close()
		yield self.protocol.close()
	
	@defer.inlineCallbacks
	def get_message(self):
		log.debug("[a] looking for message")
		msg = yield self.queue.get()
		defer.returnValue(json.loads(msg.content.body))
	
	def send_message(self, routing_key, msg):
		from txamqp import content
		log.warning('[a] sending %s to %s' % (msg, routing_key))
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
