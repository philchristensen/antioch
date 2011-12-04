import urllib

from zope import interface

from twisted.application import internet, service
from twisted.internet import defer, reactor, protocol
from twisted.web.client import HTTPClientFactory

import restmq.web

from antioch.core import parser
from antioch import messaging, conf, json

def getService(queue_url, profile=False):
	restmq_service = RestMQService(queue_url, profile=profile)
	restmq_service.setName("message-service")
	return restmq_service

def installServices(master_service, queue_url, profile=False):
	url = parser.URL(queue_url)
	if(url['host'] not in ('localhost', '127.0.0.1', '::1')):
		warnings.warn("Builtin messaging server not bound to localhost. Shouldn't you be using RabbitMQ instead?")
	
	restmq_server = internet.TCPServer(int(url['port']),
		restmq.web.Application('acl.conf',
			conf.get('redis-host'), conf.get('redis-port'),
			conf.get('redis-pool'), conf.get('redis-db')
		),
		interface = url['host'],
	)
	restmq_server.setName("message-server")
	restmq_server.setServiceParent(master_service)
	
	getService(queue_url, profile=profile).setServiceParent(master_service)

class RestMQService(service.Service):
	"""
	Provides a service that holds a reference to the active
	RestMQ connection.
	"""
	interface.implements(messaging.IMessageService)

	def __init__(self, queue_url, profile=False):
		self.queue_url = queue_url
		self.profile = profile
		self.url = parser.URL(queue_url)
		if(self.url['scheme'] != 'restmq'):
			raise RuntimeError("Unsupported scheme %r" % self.url['scheme'])

	def get_queue(self, user_id):
		"""
		Get a queue object that stores up messages until committed.
		"""
		q = RestMQQueue(self, user_id, self.profile)
		q.queue_url = self.queue_url
		return q

class RestMQQueue(messaging.AbstractQueue):
	def start(self):
		#declare channel with self.user_id
		return defer.succeed(True)

	def stop(self):
		#kill channel with self.user_id
		return defer.succeed(True)

	@defer.inlineCallbacks
	def pop(self):
		return self._get()
	
	@defer.inlineCallbacks
	def _pop(self, return_list=False):
		"""
		Take one item from this user's queue.
		"""
		queue_url = parser.URL(self.queue_url)
		url = 'http://%(host)s:%(port)s/queue' % dict(
			host	= queue_url['host'],
			port	= queue_url['port'],
		)
		
		result = []
		reading = True
		while(reading):
			client = HTTPClientFactory(url, **dict(
				method		= 'POST',
				headers		= {
					'Content-Type'	: 'application/x-www-form-urlencoded',
				},
				postdata	= urllib.urlencode(dict(
					msg		= json.dumps(dict(
						cmd		= "take",
						queue	= 'user-%s' % self.user_id,
					)),
				)),
			))
			client.noisy = False
		
			reactor.connectTCP(queue_url['host'], int(queue_url['port']), client)
			response = yield client.deferred
			response = json.loads(response)
		
			if('error' in response):
				if(response['error'] == 'empty queue'):
					defer.returnValue(result if return_list else None)
				else:
					raise RuntimeError('restmq-pop-error: %s' % response)
			result.append(json.loads(response['value'].decode('utf8')))
			if not(return_list):
				break
		
		defer.returnValue(result[0])

	def get_available(self):
		return self._pop(return_list=True)

	@defer.inlineCallbacks
	def flush(self):
		"""
		Send all queued messages.
		"""
		queue_url = parser.URL(self.queue_url)
		url = 'http://%(host)s:%(port)s/queue' % dict(
			host	= queue_url['host'],
			port	= queue_url['port'],
		)
		
		for msg in self.messages:
			client = HTTPClientFactory(url, **dict(
				method		= 'POST',
				headers		= {
					'Content-Type'	: 'application/x-www-form-urlencoded',
				},
				postdata	= urllib.urlencode(dict(
					msg		= json.dumps(dict(
						cmd		= 'add',
						queue	= 'user-%s' % msg[0],
						value	= json.dumps(msg[1]),
					)),
				)),
			))
			client.noisy = False
			
			reactor.connectTCP(queue_url['host'], int(queue_url['port']), client)
			response = yield client.deferred
			response = json.loads(response)
			
			if('error' in response):
				raise RuntimeError('restmq-flush-error: %s' % response)
