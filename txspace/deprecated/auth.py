# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Auth


This module contains all the classes used in the Twisted Cred
authentication framework, and some other security-related things.
"""

from zope.interface import implements

from twisted.cred import checkers, credentials
from twisted.cred import error
from twisted.internet import defer
from twisted.python import failure

from twisted.application import service

from txspace import errors, security, transact
from txspace.security import Q

class RegistryService(service.Service):
	"""
	Provides a service that holds a reference to the active
	registry object.
	"""
	def __init__(self, registry):
		"""
		Create a service with the given registry.
		"""
		self.registry = registry

class RegistryChecker(object):
	"""
	This class allows us to authenticate against objects in
	the registry.
	"""
	implements(checkers.ICredentialsChecker)
	
	credentialInterfaces = (credentials.IUsernamePassword,
		credentials.IUsernameHashedPassword)
	
	def __init__(self, registry):
		"""
		Create a checker with the given registry.
		"""
		self.registry = registry
	
	def _cbPasswordMatch(self, matched, avatarId):
		"""
		A helper function that returns a Failure if the
		user did not authenticate correctly, and the id
		of their character object if he did.
		"""
		if matched:
			return avatarId
		else:
			return failure.Failure(error.UnauthorizedLogin())
	
	def requestAvatarId(self, credentials):
		"""
		This function is called after the user has submitted
		authentication credentials (in this case, a user name
		and password).
		"""
		refs = self.registry.refs(credentials.username)
		try:
			user = None
			system = self.registry.get(0)
			if(hasattr(credentials, 'challenge')):
				password = credentials.challenge
			else:
				password = credentials.password
			
			if(system.has_callable_verb(Q, 'authenticate')):
				user = system.call_verb(Q, 'authenticate', credentials.username, password)
				if(isinstance(user, str)):
					return failure.Failure(error.UnauthorizedLogin(user))
				if(user):
					return user.get_id()
			
			user = self.registry.get(credentials.username)
			if(not user or user.is_connected_player(Q)):
				if not(security.is_allowed(user, 'multi_login', user)):
					return failure.Failure(error.UnauthorizedLogin())
			if(user.is_player(Q) and user.has_property(Q, "passwd", False)):
				result = credentials.checkPassword(user._vdict['passwd'].get_value(Q))
				if(isinstance(result, defer.Deferred)):
					result.addCallback(self._cbPasswordMatch, user.get_id(Q))
				elif(not isinstance(result, failure.Failure)):
					result = self._cbPasswordMatch(result, user.get_id(Q))
				return result
		except errors.AmbiguousObjectError, e:
			return failure.Failure(e);
		return failure.Failure(error.UnauthorizedLogin())

class TransactionChecker(object):
	"""
	This class allows us to authenticate against objects in
	the database.
	"""
	implements(checkers.ICredentialsChecker)
	
	credentialInterfaces = (credentials.IUsernamePassword,
		credentials.IUsernameHashedPassword,
		credentials.IAnonymous)
	
	@defer.inlineCallbacks
	def requestAvatarId(self, creds):
		"""
		This function is called after the user has submitted
		authentication credentials (in this case, a user name
		and password).
		"""
		if(credentials.IUsernamePassword.providedBy(creds)):
			result = yield transact.Authenticate.run(username=creds.username, password=creds.password)
			if(result['user_id'] == -1):
				defer.returnValue(failure.Failure(error.UnauthorizedLogin(result['error'])))
			defer.returnValue(result['user_id'])
