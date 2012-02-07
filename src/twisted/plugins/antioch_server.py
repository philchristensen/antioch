# antioch
# Copyright (c) 1999-2011 Phil Christensen
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

from antioch import conf
conf.init()

class antiochServer(object):
	"""
	The antioch application server startup class.
	"""
	
	classProvides(service.IServiceMaker, plugin.IPlugin)
	
	tapname = "antioch"
	description = "Run an antioch appserver."
	
	class options(usage.Options):
		"""
		Option-parsing for the antioch twistd plugin.
		"""
		optFlags =		[["with-client", "c", "Use the internal WSGI/Django-powered frontend client."],
						]
	
	@classmethod
	def makeService(cls, config):
		"""
		Setup the necessary network services for the application server.
		"""
		if(conf.get('suppress-deprecation-warnings')):
			warnings.filterwarnings('ignore', r'.*', DeprecationWarning)
		
		class PythonLoggingMultiService(service.MultiService):
			def setServiceParent(self, parent):
				service.MultiService.setServiceParent(self, parent)
				observer = log.PythonLoggingObserver(loggerName='antioch')
				parent.setComponent(log.ILogObserver, observer.emit)
		
		master_service = PythonLoggingMultiService()
		
		from antioch import messaging
		messaging.installServices(master_service, conf.get('queue-url'), conf.get('profile-queue'))
		msg_service = master_service.getServiceNamed('message-service')	
		
		from antioch.core import tasks
		task_service = tasks.TaskService()
		task_service.setName("task-daemon")
		task_service.setServiceParent(master_service)
		
		from antioch.core import appserver
		app_service = appserver.AppServer(msg_service)
		app_service.setName("app-server")
		app_service.setServiceParent(master_service)
		
		if(config['with-client']):
			from antioch import client
			web_service = client.DjangoServer(msg_service)
			web_service.setName("django-server")
			web_service.setServiceParent(master_service)
		
		task_service.run()
		
		return master_service
