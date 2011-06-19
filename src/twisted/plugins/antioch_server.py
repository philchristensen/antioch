# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
twistd plugin support

This module adds a 'antioch' server type to the twistd service list.
"""

import warnings

from zope.interface import classProvides

from twisted import plugin
from twisted.python import usage, log
from twisted.internet import reactor
from twisted.application import internet, service

from antioch import conf, parser

class antiochServer(object):
	"""
	The antioch application server startup class.
	"""

	classProvides(service.IServiceMaker, plugin.IPlugin)

	tapname = "antioch"
	description = "Run a set of antioch servers."

	class options(usage.Options):
		"""
		Implement option-parsing for the antioch twistd plugin.
		"""
		optParameters = [
						 ["conf", "f", conf.DEFAULT_CONF_PATH, "Path to configuration file, if any.", str],
						]

	@classmethod
	def makeService(cls, config):
		"""
		Setup the necessary network services for the application server.
		"""
		if(conf.get('suppress-deprecation-warnings')):
			warnings.filterwarnings('ignore', r'.*', DeprecationWarning)

		error_log = conf.get('error-log')
		if(error_log):
			log.startLogging(open(error_log, 'w'))
		else:
			from antioch import logging
			reactor.addSystemEventTrigger('after', 'startup', logging.customizeLogs)

		master_service = service.MultiService()

		from antioch import messaging
		msg_service = messaging.makeService(conf.get('queue-url'), conf.get('profile-queue'))
		msg_service.setName("message-client")
		msg_service.setServiceParent(master_service)

		queue_url = parser.URL(conf.get('queue-url'))
		if(queue_url['scheme'] == 'restmq'):
			import restmq.web
			if(queue_url['host'] not in ('localhost', '127.0.0.1', '::1')):
				warnings.warn("Builtin messaging server not bound to localhost. Shouldn't you be using RabbitMQ instead?")
		
			restmq_service = internet.TCPServer(int(queue_url['port']),
				restmq.web.Application('acl.conf',
					conf.get('redis-host'), conf.get('redis-port'),
					conf.get('redis-pool'), conf.get('redis-db')
				),
				interface = queue_url['host'],
			)
			restmq_service.setName("message-server")
			restmq_service.setServiceParent(master_service)

		from antioch import tasks
		task_service = tasks.TaskService()
		task_service.setName("task-daemon")
		task_service.setServiceParent(master_service)

		from antioch import web
		web_service = web.WebService(msg_service, conf.get('db-url-default'), conf.get('access-log'))
		web_service.setName("web-server")
		web_service.setServiceParent(master_service)

		task_service.run()

		return master_service
