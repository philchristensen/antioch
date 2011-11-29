# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Authenticate against the relational database
"""

from zope.interface import implements

from twisted.cred import checkers, credentials
from twisted.cred import error
from twisted.internet import defer
from twisted.python import failure, log

from antioch import transact, errors

class TransactionChecker(object):
	"""
	This class allows us to authenticate against objects in the database.
	"""
	implements(checkers.ICredentialsChecker)
	
	credentialInterfaces = (credentials.IUsernamePassword,
		credentials.IUsernameHashedPassword,
		credentials.IAnonymous)
	
	def __init__(self, db_url=None):
		"""
		Check credentials against the database specified by the provided db_url.
		
		@param db_url: the database connection string in the form C{moduleName://user:pass@hostname/databaseName}
		@type db_url: str
		"""
		self.db_url = db_url
	
	@defer.inlineCallbacks
	def requestAvatarId(self, creds):
		"""
		This function is called after the user has submitted
		authentication credentials (in this case, a user name
		and password).
		
		@param creds: the credentials of the authenticating user
		@type creds: L{twisted.cred.credentials.IUsernamePassword} implementor
		"""
		if(credentials.IUsernamePassword.providedBy(creds)):
			try:
				result = yield transact.Authenticate.run(db_url=self.db_url, username=creds.username, password=creds.password, ip_address=creds.ip_address)
				defer.returnValue(result['user_id'])
			except errors.PermissionError, e:
				raise error.UnauthorizedLogin(str(e))

class DjangoBackend:
	"""
	Authenticate against the antioch object database.
	"""
	supports_object_permissions = False
	supports_anonymous_user = True
	supports_inactive_user = False

	def authenticate(self, username=None, password=None, request=None):
		import crypt
		from antioch.client.models import Player
		
		try:
			p = Player.objects.filter(
				avatar__name__iexact = username,
			)[:1]
			
			if not(p):
				log.msg("Django auth failed.")
				return None
			
			p = p[0]
			if(p.crypt != crypt.crypt(password, p.crypt[0:2])):
				return None
			return p
		except Player.DoesNotExist:
			log.msg("Player auth failed.")
			return None
		except Exception, e:
			import traceback
			e = traceback.format_exc()
			log.msg("Error in authenticate(): %s" % e)

	def get_user(self, user_id):
		from antioch.client.models import Player
		
		try:
			p = Player.objects.get(pk=user_id)
			if(p):
				return p
			return None
		except Player.DoesNotExist:
			return None

