import urllib

from zope import interface

from twisted.application import internet, service
from twisted.internet import defer, reactor, protocol
from twisted.web.client import HTTPClientFactory

from antioch import messaging, conf
from antioch.core import parser
from antioch.util import json

def getService(queue_url, profile=False):
	ironmq_service = IronMQService(queue_url, profile=profile)
	ironmq_service.setName("message-service")
	return ironmq_service

def installServices(master_service, queue_url, profile=False):
	getService(queue_url, profile=profile).setServiceParent(master_service)

class IronMQService(service.Service):
	"""
	Provides a service that holds a reference to the active
	ironmq connection.
	"""
	interface.implements(messaging.IMessageService)

	def __init__(self, queue_url, profile=False):
		self.queue_url = queue_url
		self.profile = profile
		self.url = parser.URL(queue_url)
		if(self.url['scheme'] != 'ironmq'):
			raise RuntimeError("Unsupported scheme %r" % self.url['scheme'])

	def get_queue(self, user_id):
		"""
		Get a queue object that stores up messages until committed.
		"""
		q = IronMQueue(self, user_id, self.profile)
		q.queue = IronMQ(
			token = conf.get('ironmq-token'),
			project_id = conf.get('ironmq-project-id'),
		)
		return q

class IronMQueue(messaging.AbstractQueue):
	def start(self):
		#declare channel with self.user_id
		return defer.succeed(True)

	def stop(self):
		#kill channel with self.user_id
		return defer.succeed(True)

	@defer.inlineCallbacks
	def pop(self):
		return self._pop()
	
	@defer.inlineCallbacks
	def _pop(self, return_list=False):
		"""
		Take one item from this user's queue.
		"""
		url = "%(protocol)s://%(host)s:%(port)s/%(version)s/" % self.queue.__dict__
		
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
					raise RuntimeError('ironmq-pop-error: %s' % response)
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
		self.queue_url
		url = "%s://%s:%s/%s/" % (self.protocol, self.host, self.port,
                self.version)
		
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
				raise RuntimeError('ironmq-flush-error: %s' % response)