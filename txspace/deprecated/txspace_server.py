# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

from zope.interface import classProvides

from twisted import plugin
from twisted.python import usage

from twisted.cred import portal, checkers, credentials
from twisted.internet import reactor
from twisted.application import internet, service

from txspace import auth, external, registry, assets

class txSpaceServer(object):
	classProvides(service.IServiceMaker, plugin.IPlugin)
	
	tapname = "txspace"
	description = "Run a set of txspace servers."
	
	class options(usage.Options):
		optParameters = [
						 ["web-port", "W", 8080, "Port to use for web server.", int],
						 ["ssh-port" ,"S", 8022, "Port to use for SSH/manhole server.", int],
						 ["datafile", "f", 'universe.xml', "An XML datafile to bootstrap with.", str],
						 ["verbdir", "v", assets.get_verbdir(), "A directory of verbs to bootstrap with.", str],
						 ["accesslog", "l", '-', "Path to access log.", str],
						]
	
	@classmethod
	def makeService(cls, config):
		master_service = service.MultiService()
		
		reg_service = auth.RegistryService(registry.Registry(True))
		reg_service.setName("registry")
		reg_service.setServiceParent(master_service)
		
		load_path = config['datafile']
		save_path = external.rotate_datafile(load_path)
		
		if not(external.load(reg_service.registry, load_path)):
			from txspace import minimal
			reg_service.registry = registry.Registry()
			minimal.init(reg_service.registry, config['verbdir'])
		
		reactor.addSystemEventTrigger('before', 'shutdown', external.save, reg_service.registry, save_path)
		
		checker = auth.RegistryChecker(reg_service.registry)
		
		web_factory = cls.makeWebFactory(checker, reg_service, config['accesslog'])
		web_service = internet.TCPServer(int(config['web-port']), web_factory)
		web_service.setServiceParent(master_service)
		
		try:
			manhole_factory = cls.makeManholeFactory(checker, reg_service)
			manhole_service = internet.TCPServer(int(config['ssh-port']), manhole_factory)
			manhole_service.setServiceParent(master_service)
		except Exception, e:
			import sys
			print >>sys.stderr, "Couldn't start the manhole service because of an exception: %s" % e
		
		return master_service
	
	@classmethod
	def makeManholeFactory(cls, checker, service):
		from twisted.conch import manhole_ssh
		from txspace.auth import manhole
		
		manhole_portal = portal.Portal(manhole.Realm(service))
		manhole_portal.registerChecker(checker)
		
		factory = manhole_ssh.ConchFactory(manhole_portal)
		
		return factory
	
	@classmethod
	def makeWebFactory(cls, checker, service, accesslog):
		from nevow import guard, appserver
		from txspace.client import web as webclient
		from txspace.client.web import session
		
		pool = session.InMemoryUserSessionStore(service.registry)
		
		web_portal = portal.Portal(session.SessionRealm(pool))
		web_portal.registerChecker(session.SessionChecker(pool))
		
		site_root = webclient.RootDelegatePage(pool, web_portal)
		
		if(accesslog != '-'):
			factory = appserver.NevowSite(site_root, logPath=accesslog)
		else:
			factory = appserver.NevowSite(site_root)
		
		return factory
