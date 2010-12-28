# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Enable access to the messaging server
"""

import pkg_resources as pkg

from twisted.application import service
from twisted.internet import defer, reactor
from twisted.internet.protocol import ClientCreator

import time

from txamqp import spec, protocol, content
from txamqp.client import TwistedDelegate

from antioch import assets, json

profile_messages = False

AMQP_HOST = 'localhost'
AMQP_PORT = 5672
AMQP_VHOST = '/'
AMQP_USER = 'guest'
AMQP_PASS = 'guest'

class MessageService(service.Service):
	"""
	Provides a service that holds a reference to the active
	AMQP connection.
	"""
	def __init__(self):
		"""
		Create a service with the given connection.
		"""
		s = spec.loadString(pkg.resource_string('antioch.assets', 'amqp-specs/amqp0-8.xml'), 'amqp0-8.xml')
		self.factory = ClientCreator(reactor, protocol.AMQClient, delegate=TwistedDelegate(), vhost=AMQP_VHOST, spec=s)
		self.connection = None
		self.channel_counter = 0
	
	def get_queue(self):
		"""
		Get a queue object that stores up messages until committed.
		"""
		return MessageQueue(self)
	
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
			# print 'connecting %s' % self
			self.connection = yield self.factory.connectTCP(AMQP_HOST, AMQP_PORT)
			yield self.connection.authenticate(AMQP_USER, AMQP_PASS)
	
	@defer.inlineCallbacks
	def disconnect(self):
		"""
		Disconnect from the AMQP server.
		"""
		# print 'disconnecting %s' % self
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
		#print 'opened channel %s on %s' % (chan, self)
		yield chan.channel_open()
		defer.returnValue(chan)

class MessageQueue(object):
	"""
	Encapsulate and queue messages during a database transaction.
	"""
	def __init__(self, service):
		"""
		Create a new queue for the provided service.
		"""
		self.service = service
		self.queue = []
	
	def send(self, user_id, msg):
		"""
		Send a message to a certain user.
		"""
		self.queue.append((user_id, msg))
	
	@defer.inlineCallbacks
	def commit(self):
		"""
		Send all queued messages and close the channel.
		"""
		t = time.time()
		
		yield self.service.connect()
		if(profile_messages):
			print '[messages] connect took %s seconds' % (time.time() - t)
			t = time.time()
		
		exchange = 'user-exchange'
		chan = yield self.service.open_channel()
		if(profile_messages):
			print '[messages] channel open took %s seconds' % (time.time() - t)
			t = time.time()
		# yield chan.exchange_declare(exchange=exchange, type="direct", durable=False, auto_delete=True)
		while(self.queue):
			user_id, msg = self.queue.pop(0)
			routing_key = 'user-%s' % user_id
			data = json.dumps(msg)
			c = content.Content(data, properties={'content type':'application/json'})
			yield chan.basic_publish(exchange=exchange, content=c, routing_key=routing_key)
		yield chan.channel_close()
		if(profile_messages):
			print '[messages] purging queue took %s seconds' % (time.time() - t)
			t = time.time()
	
	