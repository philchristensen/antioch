# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
twistd plugin support

This module adds a 'antioch' server type to the twistd service list.
"""

from zope.interface import classProvides

from twisted import plugin
from twisted.python import usage, log
from twisted.internet import reactor
from twisted.application import internet, service

from antioch import conf

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
			import warnings
			warnings.filterwarnings('ignore', r'.*', DeprecationWarning)

		error_log = conf.get('error-log')
		if(error_log):
			log.startLogging(open(error_log, 'w'))
		else:
			from antioch import logging
			reactor.addSystemEventTrigger('after', 'startup', logging.customizeLogs)

		master_service = service.MultiService()

		from antioch import messaging
		msg_service = messaging.MessageService(conf.get('queue-url'), conf.get('profile-queue'))
		msg_service.setName("message-interface")
		msg_service.setServiceParent(master_service)

		from antioch import tasks
		task_service = tasks.TaskService()
		task_service.setName("task-interface")
		task_service.setServiceParent(master_service)

		from antioch import web
		web_service = web.WebService(msg_service, conf.get('db-url-default'), conf.get('access-log'))
		web_service.setName("web-interface")
		web_service.setServiceParent(master_service)

		reactor.addSystemEventTrigger('before', 'shutdown', msg_service.disconnect)
		task_service.run()

		return master_service
