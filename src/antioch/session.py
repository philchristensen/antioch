# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Database-resident web session support.

Notes About "Infant" Sessions:

Sessions will not be added to the session store until a second request
is made providing the session cookie. Until that time, they are kept in
the INFANT_SESSIONS dict. This dict could get rather large, depending on
how many of the bots you get are cookie-aware, and their requests may
end up creating numerous fake sessions. It could be neccessary to purge
the infant session cache more frequently than the session store.

Another option for dealing with this is to simply not save the session
unless a user_id is being set, because in our case that means the user
must support cookies. I'd rather this session code be more generally
useful, though, and I like the idea of sessions for anonymous users.

If, on the other hand, you'd rather just leave everything in a relational
database, or are running multiple web servers from the same DB, you probably
will want to set QUARANTINE_INFANT_SESSIONS to False.

@var COOKIE_KEY: the session cookie name
@type COOKIE_KEY: str

@var CLEANUP_CHANCE: the odds that old sessions will be cleanup during this request
@type CLEANUP_CHANCE: int

@var QUARANTINE_INFANT_SESSIONS: should new sessions be quarantined until they are used a second time?
@type QUARANTINE_INFANT_SESSIONS: bool

@var INFANT_SESSIONS: holding area for new sessions
@type INFANT_SESSIONS: dict(str => dict)

@var INFANT_SESSION_TIMEOUT: if a session hasn't been verified in this long, remove it
@type INFANT_SESSION_TIMEOUT: int
"""

import time, datetime, random, os

from zope.interface import implements, Interface

from twisted.python import log
from twisted.internet.defer import inlineCallbacks, returnValue, maybeDeferred, Deferred
from twisted.cred import portal, checkers, credentials

from nevow import inevow, rend

from antioch import auth, dbapi, transact, sql, conf

COOKIE_KEY = 'sid'
CLEANUP_CHANCE = 100

QUARANTINE_INFANT_SESSIONS = False
INFANT_SESSIONS = {}
INFANT_SESSION_TIMEOUT = 3600

try:
	import hashlib
	hash_cookie = hashlib.md5
except ImportError:
	import md5
	hash_cookie = md5.new

def createSessionCookie(request=None):
	"""
	Make a number based on current time, pid, remote ip
	and two random ints, then hash with md5. This should
	be fairly unique and very difficult to guess.
	"""
	t = long(time.time()*10000)
	pid = os.getpid()
	rnd1 = random.randint(0, 999999999)
	rnd2 = random.randint(0, 999999999)
	if(request is None):
		import socket
		ip = socket.gethostname()
	else:
		ip = request.getClientIP()
	
	return hash_cookie("%d%d%d%d%s" % (t, pid, rnd1, rnd2, ip)).hexdigest()

@inlineCallbacks
def destroySession(pool, request):
	"""
	Destroy the current session for this request.
	
	Delete the session record and remove the session cookie.
	"""
	sid = request.getCookie(COOKIE_KEY)
	if(sid):
		date = time.strftime("%a, %d-%b-%Y %H:%M:%S GMT", time.gmtime(time.time() - 86400))
		request.addCookie(COOKIE_KEY, '', path='/', expires=date)
		yield maybeDeferred(pool.destroySession, sid)
	
	returnValue(None)

@inlineCallbacks
def updateSession(pool, request, user=None):
	"""
	Update the access time and/or user_id for this session.
	
	This function will first attempt to find the session in the infant
	session cache, removing it (and saving it to DB) if found.
	
	updateSession is also responsible for setting the session cookie
	if it doesn't yet exist.
	
	@param pool: the database connection to use.
	@type pool: L{IUserSessionStore}
	
	@param request: the current request.
	@type request: L{nevow.appserver.NevowRequest}
	
	@param user: the current user record, if any
	@type user: dict
	"""
	sid = request.getCookie(COOKIE_KEY)
	if not(sid):
		sid = createSessionCookie(request)
		request.addCookie(COOKIE_KEY, sid, path='/')
	
	if(sid in INFANT_SESSIONS):
		session = INFANT_SESSIONS[sid]
		del INFANT_SESSIONS[sid]
	else:
		session = yield maybeDeferred(pool.loadSession, sid)
	
	if(session and (session['accessed'] - session['created']).seconds > session['timeout']):
		destroySession(pool, request)
		sid = createSessionCookie(request)
		request.addCookie(COOKIE_KEY, sid, path='/')
		user = None
		session = None
	
	if not(session):
		session = dict(
			id = sid,
			user_id = None,
			created = datetime.datetime.now(),
			timeout = 3600,
			data = None,
		)
		if(QUARANTINE_INFANT_SESSIONS):
			INFANT_SESSIONS[sid] = session
	
	session['accessed'] = datetime.datetime.now()
	session['last_client_ip'] = request.getClientIP()
	if(user):
		session['user_id'] = user['avatar_id']
	
	if(sid not in INFANT_SESSIONS):
		yield maybeDeferred(pool.saveSession, session)
	
	if(random.randint(1, CLEANUP_CHANCE) == 1):
		_cleanupInfantSessions()
		log.msg('Expiring abandoned sessions')
		pool.cleanupSessions()

def getSessionCredentials(ctx):
	"""
	Given a Nevow context object, return a SessionCredentials object.
	
	@param ctx: the current context
	@type ctx: L{nevow.context.WebContext}
	
	@return: the session credentials
	@rtype: L{SessionCredentials} or L{twisted.cred.credentials.Anonymous}
	"""
	request = inevow.IRequest(ctx)
	cookie = request.getCookie(COOKIE_KEY)
	if(cookie):
		creds = SessionCredentials(cookie)
	else:
		creds = credentials.Anonymous()
	return creds

def _cleanupInfantSessions():
	"""
	Iterate through the infant session cache and remove expired sessions.
	"""
	for sid, session in INFANT_SESSIONS.items():
		if(time.time() - session['created'] > INFANT_SESSION_TIMEOUT):
			log.msg('Expiring infant session %s' % sid)
			del INFANT_SESSIONS[sid]

class IUserSessionStore(Interface):
	def loadUser(self, avatarId):
		"""
		Return the user object for this user_id.
		
		@param user_id: the user ID to load.
		@type user_id: int
		
		@return: the user object
		"""
	
	def verifyLogin(self, credentials):
		"""
		Get the user_id for the provided username and password credentials.
		
		@param credentials: the login credentials
		@type credentials: str
		
		@return: the user_id, or None
		@rtype: int
		"""
	
	def loadSession(self, sid):
		"""
		Return the session record for this user_id.
		
		@param user_id: the user ID to load.
		@type user_id: int
		
		@return: the session record
		@rtype: dict
		"""
	
	def verifySession(self, sid):
		"""
		Get the user_id for the provided session ID.
		
		@param sid: the login session ID
		@type sid: str
		
		@return: the user_id, or None
		@rtype: int
		"""
	
	def saveSession(self, session):
		"""
		Save the provided session record.
		
		@param session: the session record to save
		@type session: dict
		
		@return: True if there were no errors.
		"""
	
	def destroySession(self, sid):
		"""
		Remove expired sessions from the database.
		"""
	
	def cleanupSessions(self):
		"""
		Remove expired sessions from the database.
		"""

class InMemoryUserSessionStore(object):
	"""
	An IUserSessionStore that does not persist sessions between startups.
	"""
	
	implements(IUserSessionStore)
	
	def __init__(self, registry):
		"""
		Create the in-memory session store.
		"""
		self.sessions = {}
		self.registry = registry
		self.checker = auth.RegistryChecker(registry)
	
	def loadUser(self, avatarId):
		"""
		@see: L{IUserSessionStore.loadUser()}
		"""
		if(avatarId is None):
			return None
		return self.registry.get(avatarId)
	
	def logoutUser(self, sid):
		if(sid in self.sessions):
			self.sessions.pop(sid)
	
	def verifyLogin(self, credentials):
		"""
		@see: L{IUserSessionStore.verifyLogin()}
		"""
		return self.checker.requestAvatarId(credentials)
	
	def loadSession(self, sid):
		"""
		@see: L{IUserSessionStore.loadSession()}
		"""
		return self.sessions.get(sid)
	
	def verifySession(self, sid):
		"""
		@see: L{IUserSessionStore.verifySession()}
		"""
		if(sid in self.sessions):
			return self.sessions[sid]['user_id']
		return None
	
	def saveSession(self, session):
		"""
		@see: L{IUserSessionStore.saveSession()}
		"""
		self.sessions[session['id']] = session
		return True
	
	def destroySession(self, sid):
		"""
		@see: L{IUserSessionStore.destroySession()}
		"""
		self.sessions.remove(sid)
	
	def cleanupSessions(self):
		"""
		@see: L{IUserSessionStore.cleanupSessions()}
		"""
		for sid, session in self.sessions.items():
			if(session['accessed'] - session['created'] > session['timeout']):
				del self.sessions[sid]

class TransactionUserSessionStore(object):
	"""
	An IUserSessionStore that uses a relational database while supporting custom authenticate verbs.
	"""
	
	implements(IUserSessionStore)
	
	def __init__(self, checker, db_url):
		"""
		Create the in-memory session store.
		"""
		self.checker = checker
		self.pool = dbapi.connect(db_url, **dict(
			async			= True,
			debug			= conf.get('debug-sql'),
			debug_writes	= conf.get('debug-sql-writes'),
			debug_syntax	= conf.get('debug-sql-syntax'),
			profile			= conf.get('profile-db'),
		))
	
	@inlineCallbacks
	def loadUser(self, avatarId):
		"""
		@see: L{IUserSessionStore.loadUser()}
		"""
		if(avatarId is None):
			returnValue(None)
		result = yield self.pool.runQuery("SELECT * FROM player WHERE avatar_id = %s", [avatarId])
		if not(result):
			returnValue(None)
		returnValue(result[0])
	
	@inlineCallbacks
	def logoutUser(self, sid):
		yield self.pool.runOperation("DELETE FROM session WHERE id = %s", [sid])
	
	@inlineCallbacks
	def verifyLogin(self, credentials):
		"""
		@see: L{IUserSessionStore.verifyLogin()}
		"""
		result = yield self.checker.requestAvatarId(credentials)
		returnValue(result)
	
	@inlineCallbacks
	def loadSession(self, sid):
		"""
		@see: L{IUserSessionStore.loadSession()}
		"""
		result = yield self.pool.runQuery("SELECT * FROM session WHERE id = %s", [sid])
		if not(result):
			returnValue(None)
		returnValue(result[0])
	
	@inlineCallbacks
	def verifySession(self, sid):
		"""
		@see: L{IUserSessionStore.verifySession()}
		"""
		result = yield self.pool.runQuery("SELECT user_id FROM session WHERE id = %s", [sid])
		result = result or [{'user_id':None}]
		returnValue(result[0]['user_id'])
	
	@inlineCallbacks
	def saveSession(self, session):
		"""
		@see: L{IUserSessionStore.saveSession()}
		"""
		result = yield self.pool.runQuery(sql.interp("SELECT 1 FROM session WHERE id = %s", session['id']))
		if(result):
			yield self.pool.runOperation(sql.build_update('session', session, dict(id=session['id'])))
		else:
			yield self.pool.runOperation(sql.build_insert('session', session))
		returnValue(True)
	
	@inlineCallbacks
	def destroySession(self, sid):
		"""
		@see: L{IUserSessionStore.destroySession()}
		"""
		yield self.pool.runOperation("DELETE FROM session WHERE id = %s", [sid])
	
	@inlineCallbacks
	def cleanupSessions(self):
		"""
		@see: L{IUserSessionStore.cleanupSessions()}
		"""
		yield self.pool.runOperation("DELETE FROM session WHERE extract('epoch' from accessed - created) > timeout")

class SessionRealm(object):
	"""
	This Realm will choose the appropriate delegate Resource
	to reflect the authentication state.

	@ivar pool: the current session pool
	@type pool: L{IUserSessionStore}
	"""
	implements(portal.IRealm)
	
	def __init__(self, pool):
		"""
		Create a new realm that can authenticate against the provided session pool.
		
		@param pool: the current session pool
		@type pool: L{IUserSessionStore}
		"""
		self.pool = pool
	
	@inlineCallbacks
	def requestAvatar(self, avatarId, mind, *interfaces):
		"""
		@see: L{twisted.cred.portal.IRealm}
		
		@param avatarId: the authenticated user ID, or C{twisted.cred.checkers.ANONYMOUS}
		"""
		if inevow.IResource not in interfaces:
			raise NotImplementedError("no appropriate interface found")
		
		user = None
		if avatarId is not checkers.ANONYMOUS:
			user = yield maybeDeferred(self.pool.loadUser, avatarId)
		
		returnValue((inevow.IResource, user, lambda: None))

class ISessionCredentials(credentials.ICredentials):
	"""
	I represent an opaque value indicating a web session.
	"""
	def getSid(self):
		"""
		Return the session ID for these credentials.
		
		@return: the session ID
		@rtype: str
		"""
		pass

class SessionCredentials(object):
	"""
	An opaque value indicating a web session.
	"""
	implements(ISessionCredentials)

	def __init__(self, sid):
		"""
		Create a new credentials object with the provided session ID.
		
		@param sid: current session id
		"""
		self.sid = sid

	def getSid(self):
		"""
		Get the session id for these credentials.
		
		@return: the session ID
		@rtype: str
		"""
		return self.sid

class SessionChecker(object):
	"""
	Validator for web logins.
	
	A SessionChecker can handle a number of types of credentials,
	including ISessionCredentials, IUsernamePassword, and IAnonymous.
	"""
	implements(checkers.ICredentialsChecker)
	
	credentialInterfaces = (ISessionCredentials,
							credentials.IUsernamePassword,
							credentials.IAnonymous)
	
	def __init__(self, pool):
		"""
		Create a session checker for the given pool.
		
		It's assumed that the pool functions may or may not return
		Deferreds, so it's possible to use a relational database
		for the session store as well as the standard in-memory store.
		"""
		self.pool = pool
	
	def requestAvatarId(self, creds):
		"""
		@see: L{twisted.cred.checkers.ICredentialsChecker}
		"""
		if(ISessionCredentials.providedBy(creds)):
			d = self.checkSessionCredentials(creds)
		elif(credentials.IUsernamePassword.providedBy(creds)):
			d = self.checkLoginCredentials(creds)
		else:
			d = Deferred()
			d.callback(checkers.ANONYMOUS)
		return d
	
	@inlineCallbacks
	def checkSessionCredentials(self, creds):
		"""
		Return the user_id assigned to the provided session credentials.
		
		@param creds: the current session's credentials.
		@type creds: L{ISessionCredentials}
		
		@return: user_id of the authenticated user
		@rtype: int
		"""
		sid = creds.getSid()
		if(sid in INFANT_SESSIONS):
			returnValue(INFANT_SESSIONS[sid]['user_id'])
		
		result = yield maybeDeferred(self.pool.verifySession, sid)
		if(result):
			returnValue(result)
		else:
			returnValue(checkers.ANONYMOUS)
	
	@inlineCallbacks
	def checkLoginCredentials(self, creds):
		"""
		Return the user_id assigned to the provided session credentials.
		
		@param creds: the current session's credentials.
		@type creds: L{twisted.cred.credentials.IUsernamePassword}
		
		@return: user_id of the authenticated user
		@rtype: int
		"""
		result = yield maybeDeferred(self.pool.verifyLogin, creds)
		if(result):
			returnValue(result)
		else:
			returnValue(checkers.ANONYMOUS)

