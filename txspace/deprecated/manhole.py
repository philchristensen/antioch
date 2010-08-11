# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from zope.interface import implements

from twisted.cred import portal, error
from twisted.python import failure, components
from twisted.application import service

from twisted.conch import interfaces as conch_interfaces
from twisted.conch import manhole_ssh, manhole
from twisted.conch.insults import insults

from txspace import actions, auth

class Realm:
	"""
	Holds a reference to the main service object, which is, in this
	case, RegistryService.
	"""
	implements(portal.IRealm)
	
	def __init__(self, service):
		"""
		Create a realm with the given service.
		"""
		self.service = service
	
	def requestAvatar(self, avatarId, mind, *interfaces):
		"""
		This function is called after the user has verified their
		identity. It returns an object that represents the user
		in the system, i.e., an avatar.
		"""
		assert avatarId is not None, "avatarId is None"
		
		actions.handle_connect(mind)
		
		if conch_interfaces.IConchUser in interfaces:
			user = self.service.registry.get(avatarId)
			if not(user.is_wizard()):
				raise error.UnauthorizedLogin()
			comp = components.Componentized()
			user = manhole_ssh.TerminalUser(comp, avatarId)
			sess = manhole_ssh.TerminalSession(comp)
		
			sess.transportFactory = manhole_ssh.TerminalSessionTransport
		
			def manholeProtoFactory():
				return insults.ServerProtocol(manhole.ColoredManhole, namespace=dict(
					registry	= self.service.registry,
					self		= user,
				))
		
			sess.chainedProtocolFactory = manholeProtoFactory
		
			comp.setComponent(conch_interfaces.IConchUser, user)
			comp.setComponent(conch_interfaces.ISession, sess)
		
			return conch_interfaces.IConchUser, user, lambda: None
		else:
			raise NotImplementedError("no interface")
