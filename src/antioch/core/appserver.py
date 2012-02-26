# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Setup the application service.
"""

import os.path, logging

from antioch import conf
from antioch.core import messaging

import simplejson

from twisted.application import service
from twisted.internet import defer, task, reactor

log = logging.getLogger(__name__)

def get_command_support(class_name):
	from antioch import plugins
	for plugin in plugins.iterate():
		available_commands = plugin.get_commands()
		if(class_name in available_commands):
			klass = available_commands[class_name]
			child = getattr(plugin, 'transaction_child', None)
			return klass, child
	return None

class AppService(service.Service):
	def __init__(self):
		"""
		Create a new AppService.
		"""
		self.stopped = True
		self.consumer = None
		self.loop = task.LoopingCall(self.check_queue)
		self.loop.interval = 1
	
	def startService(self):
		"""
		Start the loop.
		"""
		log.info("started processing appserver queue")
		self.loop.start(self.loop.interval)
		reactor.addSystemEventTrigger("after", "startup", self._startService)
	
	@defer.inlineCallbacks
	def _startService(self):
		self.consumer = yield messaging.get_async_consumer()
		yield self.consumer.start_consuming()
		self.stopped = False
	
	def stopService(self):
		log.info("stopped processing appserver queue")
		self.stopped = True
		self.loop.stop()
		reactor.addSystemEventTrigger("before", "shutdown", self._stopService)
	
	@defer.inlineCallbacks
	def _stopService(self):
		yield self.consumer.disconnect()
	
	@defer.inlineCallbacks
	def check_queue(self, *args, **kwargs):
		if(self.stopped):
			defer.returnValue(None)
		
		msg = yield self.consumer.get_message()
		log.debug("got message from %s: %s" % (consumer, msg))
		
		klass, child = get_command_support(msg['command'])
		if(klass is None):
			defer.returnValue({'error':'No such command: %s' % msg['command']});
		
		result = yield klass.run(transaction_child=child, **msg['kwargs'])
		
		log.debug("sending response to %s: %s" % (data['responder_id'], result))
		yield consumer.send_message(data['responder_id'], result)

