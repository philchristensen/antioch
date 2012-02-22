# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Setup the application service.
"""

import os.path, logging

from antioch import conf, messaging

import simplejson

from twisted.application import service
from twisted.internet import defer, task, reactor

log = logging.getLogger(__name__)

class AppService(service.Service):
	"""
	Provides a service that iterates through queued tasks.
	
	The LoopingCall created by this service changes intervals depending on the
	success of the previous attempt. Every time a task is completed, the next
	interval before checking again is halved. If no task is found or an exception
	occurs, the time before checking again is doubled, up to MAX_DELAY seconds.
	"""
	def __init__(self, msg_service):
		"""
		Create a new TaskService.
		"""
		self.stopped = True
		self.msg_service = msg_service
		self.ident = messaging.getLocalIdent('appserver')
		self.loop = task.LoopingCall(self.check_queue)
		self.loop.interval = 1
	
	def startService(self):
		"""
		Start the loop.
		"""
		self.loop.start(self.loop.interval)
		reactor.addSystemEventTrigger("after", "startup", self._startService)
	
	@defer.inlineCallbacks
	def _startService(self):
		yield self.msg_service.connect()
		
		self.chan = yield self.msg_service.open_channel()
		yield self.chan.exchange_declare(exchange='responder', type="direct", durable=True, auto_delete=False)
		yield self.chan.queue_declare(queue='appserver', durable=True, exclusive=False, auto_delete=False)
		yield self.chan.queue_bind(queue='appserver', exchange='responder', routing_key='appserver')
		yield self.chan.basic_consume(queue='appserver', consumer_tag=self.ident, no_ack=True)
		
		log.debug('declared exchange "responder" with queue/key "appserver", consumer: %s' % (self.ident,))
		
		self.queue = yield self.msg_service.connection.queue("appserver")
		self.stopped = False
	
	def stopService(self):
		self.stopped = True
		self.loop.stop()
		reactor.addSystemEventTrigger("before", "shutdown", self._stopService)
	
	@defer.inlineCallbacks
	def _stopService(self):
		if(hasattr(self, 'chan')):
			try:
				yield self.chan.basic_cancel(self.ident)
				yield self.chan.channel_close()
			except:
				pass
		yield self.msg_service.disconnect()
	
	@defer.inlineCallbacks
	def check_queue(self, *args, **kwargs):
		"""
		Look for requests.
		"""
		if(self.stopped):
			defer.returnValue(None)
		
		from txamqp.queue import Closed as QueueClosed
		try:
			log.debug('checking for message with %s' % (self.ident,))
			msg = yield self.queue.get()
			log.debug('found message with %s: %s' % (self.ident, msg))
		except QueueClosed, e:
			defer.returnValue(None)
		
		data = simplejson.loads(msg.content.body.decode('utf8'))
		
		klass, child = get_command_support(data['command'])
		if(klass is None):
			defer.returnValue({'error':'No such command: %s' % data['command']});
		
		result = yield klass.run(transaction_child=child, **data['kwargs'])
		
		from txamqp import content
		c = content.Content(simplejson.dumps(result), properties={'content type':'application/json'})
		log.debug('returning response %s to %s' % (c, self.ident))
		yield selfchan.basic_publish(exchange="responder", content=c, routing_key=data['responder_id'])

