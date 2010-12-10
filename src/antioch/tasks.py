# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Manage asynchronous tasks.
"""

from twisted.application import service
from twisted.internet import defer, reactor, task

from antioch import transact

class TaskService(service.Service):
	"""
	Provides a service that iterates through queued tasks.
	"""
	def __init__(self):
		self.stopped = False
		self.loop = task.LoopingCall(self.check)
		self.reset_timer()
	
	def reset_timer(self):
		self.loop.interval = 1.0
	
	def run(self, result=None):
		self.loop.start(self.loop.interval)
	
	def check(self, *args, **kwargs):
		if(self.stopped):
			return
		d = transact.IterateTasks.run()
		d.addBoth(self.__check_cb)
		return d
	
	def __check_cb(self, result):
		if(result):
			self.reset_timer()
		else:
			self.loop.interval = self.loop.interval / 2 if result is None else self.loop.interval * 2
