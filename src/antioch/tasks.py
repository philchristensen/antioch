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
from twisted.python import log

from antioch import transact

MAX_DELAY = 10

class TaskService(service.Service):
	"""
	Provides a service that iterates through queued tasks.
	
	The LoopingCall created by this service changes intervals depending on the
	success of the previous attempt. Every time a task is completed, the next
	interval before checking again is halved. If no task is found or an exception
	occurs, the time before checking again is doubled, up to MAX_DELAY seconds.
	"""
	def __init__(self):
		"""
		Create a new TaskService.
		"""
		self.stopped = False
		self.loop = task.LoopingCall(self.check)
		self.reset_timer()
	
	def reset_timer(self):
		"""
		Reset the timer
		"""
		self.loop.interval = 1.0
	
	def run(self, result=None):
		"""
		Start the loop.
		"""
		self.loop.start(self.loop.interval)
	
	def check(self, *args, **kwargs):
		"""
		Attempt to execute one task.
		"""
		if(self.stopped):
			return
		d = transact.IterateTasks.run()
		d.addCallbacks(self._check_cb, self._check_eb)
		return d
	
	def _check_cb(self, result):
		"""
		Adjust the check interval based on the result.
		"""
		if(result):
			self.reset_timer()
		else:
			self.loop.interval = self.loop.interval / 2 if result is None else self.loop.interval * 2
			if(self.loop.interval > MAX_DELAY):
				self.loop.interval = MAX_DELAY
	
	def _check_eb(self, failure):
		"""
		Adjust the check interval based on the result.
		"""
		log.err("TaskService LoopingCall failed, delayed tasks will not be run.")
		self.loop.stop()
