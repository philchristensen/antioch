# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Enable access to the messaging server
"""

import logging

from zope import interface

from antioch import conf
from antioch.core import parser

log = logging.getLogger(__name__)

scheme_trans = dict(
	rabbitmq	= 'rabbitmq',
	amqp		= 'rabbitmq',
)

def getService(queue_url, profile=False):
	url = parser.URL(queue_url)
	try:
		module_name = '_' + scheme_trans[url['scheme']]
		imp = __import__('antioch.messaging', globals(), locals(), [module_name], -1)
		return getattr(imp,  module_name).getService(queue_url, profile=profile)
	except ImportError, e:
		import traceback
		traceback.print_exc()
		raise RuntimeError("Unsupported scheme %r" % url['scheme'])

def installServices(master_service, queue_url, profile=False):
	url = parser.URL(queue_url)
	try:
		module_name = '_' + scheme_trans[url['scheme']]
		imp = __import__('antioch.messaging', globals(), locals(), [module_name], -1)
		getattr(imp,  module_name).installServices(master_service, queue_url, profile=profile)
	except ImportError, e:
		import traceback
		traceback.print_exc()
		raise RuntimeError("Unsupported scheme %r" % url['scheme'])

class IMessageService(interface.Interface):
	def get_queue(user_id):
		pass

class IMessageQueue(interface.Interface):
	def pop():
		pass

	def start():
		pass

	def stop():
		pass

class AbstractQueue(object):
	"""
	Encapsulate and queue messages during a database transaction.
	"""
	interface.implements(IMessageQueue)

	def __init__(self, service, user_id, profile=False):
		"""
		Create a new queue for the provided service.
		"""
		self.profile = profile
		self.service = service
		self.user_id = user_id
		self.messages = []

	def start(self):
		raise NotImplementedError('AbstractQueue.start')

	def stop(self):
		raise NotImplementedError('AbstractQueue.stop')

	def push(self, user_id, msg):
		"""
		Send a message to a certain user.
		"""
		self.messages.append((user_id, msg))

	def pop(self):
		raise NotImplementedError('AbstractQueue.pop')

	def get_available(self):
		raise NotImplementedError('AbstractQueue.get_available')

	def flush(self):
		raise NotImplementedError('AbstractQueue.flush')

