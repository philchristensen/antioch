# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

from zope.interface import classProvides

from twisted import plugin
from twisted.python import usage

from twisted.cred import portal, checkers, credentials
from twisted.internet import reactor, defer
from twisted.application import internet, service

from txspace import auth, dbapi, messaging, tasks

class txSpaceServer(object):
	classProvides(service.IServiceMaker, plugin.IPlugin)
	
	tapname = "txspace"
	description = "Run a set of txspace servers."
	
	class options(usage.Options):
		optParameters = [
						 ["port", "p", 8080, "Port to use for web server.", int],
						 ["accesslog", "l", '-', "Path to access log.", str],
						]
		optFlags = [
					['debug', 'd', 'Debug database queries.'],
					['debug-deferreds', 'D', 'Debug Deferred objects.'],
					['debug-writes', 'w', 'Debug database writes only.'],
					]
	
	@classmethod
	def makeService(cls, config):
		if(config['debug']):
			dbapi.debug = True
		if(config['debug-writes']):
			dbapi.debug = 1
		if(config['debug-deferreds']):
			defer.Deferred.debug = True
		
		master_service = service.MultiService()
		
		msg_service = messaging.MessageService()
		msg_service.setName("message-interface")
		msg_service.setServiceParent(master_service)
		
		task_service = tasks.TaskService()
		task_service.setName("task-interface")
		task_service.setServiceParent(master_service)
		
		web_factory = cls.makeWebFactory(auth.TransactionChecker(), msg_service, config['accesslog'])
		web_service = internet.TCPServer(int(config['port']), web_factory)
		web_service.setName("client-interface")
		web_service.setServiceParent(master_service)
		
		reactor.addSystemEventTrigger('before', 'shutdown', msg_service.disconnect)
		task_service.run()
		
		return master_service
	
	@classmethod
	def makeWebFactory(cls, checker, msg_service, accesslog):
		from nevow import guard, appserver
		from txspace import client, session
		
		pool = session.TransactionUserSessionStore(checker)
		
		web_portal = portal.Portal(session.SessionRealm(pool))
		web_portal.registerChecker(session.SessionChecker(pool))
		
		site_root = client.RootDelegatePage(pool, msg_service, web_portal)
		
		if(accesslog != '-'):
			factory = appserver.NevowSite(site_root, logPath=accesslog)
		else:
			factory = appserver.NevowSite(site_root)
		
		return factory
