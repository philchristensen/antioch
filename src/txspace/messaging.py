# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import pkg_resources as pkg

from twisted.application import service
from twisted.internet import defer, reactor
from twisted.internet.protocol import ClientCreator

import simplejson, time

from txamqp import spec, protocol, content
from txamqp.client import TwistedDelegate

from txspace import assets

profile_messages = False

class MessageService(service.Service):
	"""
	Provides a service that holds a reference to the active
	AMQP connection.
	"""
	def __init__(self):
		"""
		Create a service with the given connection.
		"""
		s = spec.loadString(pkg.resource_string('txspace.assets', 'amqp-specs/amqp0-8.xml'), 'amqp0-8.xml')
		self.factory = ClientCreator(reactor, protocol.AMQClient, delegate=TwistedDelegate(), vhost='/', spec=s)
		self.connection = None
		self.channel_counter = 0
	
	def get_queue(self):
		return MessageQueue(self)
	
	@defer.inlineCallbacks
	def connect(self):
		if(self.connection):
			defer.returnValue(self.connection)
		else:
			print 'connecting %s' % self
			self.connection = yield self.factory.connectTCP('localhost', 5672)
			yield self.connection.authenticate('guest', 'guest')
	
	@defer.inlineCallbacks
	def disconnect(self):
		print 'disconnecting %s' % self
		if(self.connection):
			chan0 = yield self.connection.channel(0)
			yield chan0.connection_close()
	
	@defer.inlineCallbacks
	def open_channel(self):
		self.channel_counter += 1
		chan = yield self.connection.channel(self.channel_counter)
		#print 'opened channel %s on %s' % (chan, self)
		yield chan.channel_open()
		defer.returnValue(chan)

class MessageQueue(object):
	def __init__(self, service):
		self.service = service
		self.queue = []
	
	def send(self, user_id, msg):
		self.queue.append((user_id, msg))
	
	@defer.inlineCallbacks
	def commit(self):
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
			data = simplejson.dumps(msg)
			c = content.Content(data, properties={'content type':'application/json'})
			chan.basic_publish(exchange=exchange, content=c, routing_key=routing_key)
		yield chan.channel_close()
		if(profile_messages):
			print '[messages] purging queue took %s seconds' % (time.time() - t)
			t = time.time()
	
	