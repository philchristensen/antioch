import time, logging

import pkg_resources as pkg

from zope import interface

from twisted.python import log
from twisted.application import service
from twisted.internet import defer, reactor
from twisted.internet.protocol import ClientCreator

import simplejson

from antioch import messaging
from antioch.core import parser
from antioch.util import json

def getService(queue_url, profile=False):
	rabbitmq_service = RabbitMQService(queue_url, profile=profile)
	rabbitmq_service.setName("message-service")
	return rabbitmq_service

def installServices(master_service, queue_url, profile=False):
	getService(queue_url, profile).setServiceParent(master_service)

class RabbitMQService(service.Service):
	"""
	Provides a service that holds a reference to the active
	RebbitMQ connection.
	"""
	interface.implements(messaging.IMessageService)

	def __init__(self, queue_url, profile=False):
		"""
		Create a service with the given connection.
		"""
		self.url = parser.URL(queue_url)

		from twisted.internet.protocol import ClientCreator
		from txamqp import spec, protocol
		from txamqp.client import TwistedDelegate
		self.factory = ClientCreator(reactor, protocol.AMQClient,
			delegate = TwistedDelegate(),
			vhost	 = self.url['path'],
			spec	 = spec.loadString(
				pkg.resource_string('antioch.messaging', 'amqp-specs/amqp0-8.xml'), 'amqp0-8.xml'
			),
		)
		self.profile = profile
		self.connection = None
		self.channel_counter = 0
		
		reactor.addSystemEventTrigger('before', 'shutdown', self.disconnect)

	def get_queue(self, user_id):
		"""
		Get a queue object that stores up messages until committed.
		"""
		q = RabbitMQQueue(self, user_id, self.profile)
		return q

	@defer.inlineCallbacks
	def setup_client_channel(self, user_id):
		"""
		Instantiate the client channel for a given user.
		"""
		chan = yield self.open_channel()

		exchange = 'user-exchange'
		queue = 'user-%s-queue' % user_id
		consumertag = "user-%s-consumer" % user_id
		routing_key = 'user-%s' % user_id

		yield chan.exchange_declare(exchange=exchange, type="direct", durable=True, auto_delete=True)
		yield chan.queue_declare(queue=queue, durable=True, exclusive=False, auto_delete=True)
		yield chan.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)
		yield chan.basic_consume(queue=queue, consumer_tag=consumertag, no_ack=True)

		defer.returnValue(chan)

	@defer.inlineCallbacks
	def connect(self):
		"""
		Connect to the AMQP server.
		"""
		if(self.connection):
			defer.returnValue(self.connection)
		else:
			messaging.log.debug("connecting to RabbitMQ server at %(host)s:%(port)s with %(user)s" % self.url)
			try:
				self.connection = yield self.factory.connectTCP(self.url['host'], int(self.url['port']))
				yield self.connection.authenticate(self.url['user'], self.url['passwd'])
			except Exception, e:
				self.url['e'] = e
				raise EnvironmentError("Couldn't connect to RabbitMQ server at %(host)s:%(port)s, exception: %(e)s" % self.url)

	@defer.inlineCallbacks
	def disconnect(self):
		"""
		Disconnect from the AMQP server.
		"""
		messaging.log.debug("disconnecting from RabbitMQ server at %(host)s:%(port)s" % self.url)
		if(self.connection):
			chan0 = yield self.connection.channel(0)
			yield chan0.connection_close()

	@defer.inlineCallbacks
	def open_channel(self):
		"""
		Open a new channel to send messages.
		"""
		self.channel_counter += 1
		chan = yield self.connection.channel(self.channel_counter)
		yield chan.channel_open()
		defer.returnValue(chan)

class RabbitMQQueue(messaging.AbstractQueue):
	@defer.inlineCallbacks
	def start(self):
		conn = yield self.service.connect()
		self.chan = yield self.service.setup_client_channel(self.user_id)
		self.queue = yield self.service.connection.queue("user-%s-consumer" % self.user_id)

	@defer.inlineCallbacks
	def stop(self):
		from txamqp.client import Closed as ClientClosed
		try:
			yield self.chan.basic_cancel("user-%s-consumer" % self.user_id)
			yield self.chan.channel_close()
		except ClientClosed, ce:
			pass

	@defer.inlineCallbacks
	def pop(self):
		from txamqp.queue import Closed as QueueClosed
		data = None
		try:
			msg = yield self.queue.get()
			data = json.loads(msg.content.body.decode('utf8'))
		finally:
			defer.returnValue(data)
	
	@defer.inlineCallbacks
	def get_available(self):
		from txamqp.queue import Closed as QueueClosed
		result = []
		try:
			msg = yield self.queue.get()
			data = json.loads(msg.content.body.decode('utf8'))
			result.append(data)
		except QueueClosed, qe:
			pass
		defer.returnValue(result or None)

	@defer.inlineCallbacks
	def flush(self):
		"""
		Send all queued messages and close the channel.
		"""
		t = time.time()

		yield self.service.connect()

		if(self.profile):
			log.msg('connect took %s seconds' % (time.time() - t))
			t = time.time()

		exchange = 'user-exchange'
		chan = yield self.service.open_channel()
		if(self.profile):
			log.msg('channel open took %s seconds' % (time.time() - t))
			t = time.time()
		# yield chan.exchange_declare(exchange=exchange, type="direct", durable=False, auto_delete=True)
		while(self.messages):
			user_id, msg = self.messages.pop(0)
			routing_key = 'user-%s' % user_id
			data = json.dumps(msg)
			from txamqp import content
			c = content.Content(data, properties={'content type':'application/json'})
			yield chan.basic_publish(exchange=exchange, content=c, routing_key=routing_key)

		from txamqp.client import Closed as ClientClosed
		try:
			yield chan.channel_close()
		except ClientClosed, e:
			pass

		if(self.profile):
			log.msg('purging queue took %s seconds' % (time.time() - t))
			t = time.time()

