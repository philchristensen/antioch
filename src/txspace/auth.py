# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Auth
"""

from zope.interface import implements

from twisted.cred import checkers, credentials
from twisted.cred import error
from twisted.internet import defer
from twisted.python import failure

from txspace import transact

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
