import urllib, logging

from zope import interface

from twisted.application import internet, service
from twisted.internet import defer, reactor, protocol
from twisted.web.client import HTTPClientFactory

from antioch import messaging, conf
from antioch.core import parser
from antioch.util import json

from antioch.messaging import iron_mq

log = logging.getLogger(__name__)

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
		self.profile = profile
		# we don't save the URL since it's useless
		url = parser.URL(queue_url)
		if(url['scheme'] != 'ironmq'):
			raise RuntimeError("Unsupported scheme %r" % url['scheme'])

	def get_queue(self, user_id):
		"""
		Get a queue object that stores up messages until committed.
		"""
		q = IronMQueue(self, user_id, self.profile)
		q.queue = iron_mq.IronMQ(
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
		"""
		Take one item from this user's queue.
		"""
		log.warning('pop')
		response = yield self.queue.getMessage(queue_name="user-%s" % self.user_id, max=1)
		if(response['messages']):
			msg = response['messages'][0]
			yield self.queue.deleteMessage(queue_name="user-%s" % self.user_id, message_id=msg['id'])
			defer.returnValue(json.loads(msg['body']))
	
	@defer.inlineCallbacks
	def get_available(self):
		"""
		Get all items from this user's queue.
		"""
		fetch_size = 10
		response = dict(messages=True)
		result = []
		while(response['messages']):
			response = yield self.queue.getMessage("user-%s" % self.user_id, max=fetch_size)
			for msg in response['messages']:
				yield self.queue.deleteMessage("user-%s" % self.user_id, message_id=msg['id'])
				result.append(json.loads(msg['body']))
			if(len(response['messages']) < fetch_size):
				break
		defer.returnValue(result)

	@defer.inlineCallbacks
	def flush(self):
		"""
		Send all queued messages.
		"""
		id_map = dict()
		for m in self.messages:
			id_map.setdefault('%s' % m[0], []).append(m[1])
		
		for user_id, messages in id_map.items():
			yield self.queue.postMessage("user-%s" % user_id,
				[json.dumps(x) for x in messages],
			)
