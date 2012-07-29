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
		self.channel.confirm_delivery(lambda *args, **kwargs: None)
		log.debug("declaring exchange %s" % conf.get('appserver-exchange'))
		frame = self.channel.exchange_declare(
			exchange        = conf.get('appserver-exchange'),
			type            = 'direct',
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
			durable         = False,
			exclusive       = False,
		)
		self.channel.queue_bind(
			queue           = queue_id,
			exchange        = conf.get('appserver-exchange'),
			routing_key     = queue_id,
		)
	
	def get_messages(self, queue_id, decode=True, timeout=10):
		assert self.connected
		result = []
		check = True
		start_time = time.time()
		while(True):
			check = self.channel.basic_get(ticket=0, queue=queue_id, no_ack=True)
			if(check[0].NAME == 'Basic.GetEmpty'):
				if(result or start_time + timeout < time.time()):
					return result
				time.sleep(_blocking_sleep_interval)
			else:
				log.debug("%s received: %s" % (queue_id, check[2]))
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
