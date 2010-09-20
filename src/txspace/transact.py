# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Execution layer
"""

from twisted.python import log
from twisted.internet import defer
from twisted.protocols import amp

from ampoule import child, pool, main, util

from txspace import dbapi, exchange, errors, parser, messaging, sql, code, modules

__processPools = {}
db_url = 'psycopg2://txspace:moavmic7@localhost/txspace'

def get_process_pool(child=None, autocreate=True):
	if(child is None):
		child = DefaultTransactionChild
	
	global __processPools
	if(child.__name__ in __processPools):
		return __processPools[child.__name__]
	
	if(autocreate):
		starter = main.ProcessStarter(packages=("twisted", "ampoule"))
		__processPools[child.__name__] = pool.ProcessPool(child, name='txspace-process-pool', starter=starter)
	
	return __processPools.get(child.__name__, None)

@defer.inlineCallbacks
def shutdown(child=None):
	if(child is None):
		child = DefaultTransactionChild
	
	global __processPools
	if(child.__name__ in __processPools):
		yield __processPools[child.__name__].stop()
		del __processPools[child.__name__]

class WorldTransaction(amp.Command):
	@classmethod
	def run(cls, transaction_child=None, **kwargs):
		pool = get_process_pool(transaction_child)
		return pool.doWork(cls, **kwargs)

class Authenticate(WorldTransaction):
	arguments = [
		('username', amp.String()),
		('password', amp.String()),
	]
	response = [
		('user_id', amp.Integer()),
	]
	errors = {
		errors.PermissionError : 'PERMISSION_ERROR',
	}

class Login(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('ip_address', amp.String()),
	]
	response = [('response', amp.Boolean())]

class Logout(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
	]
	response = [('response', amp.Boolean())]

class Parse(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('sentence', amp.String()),
	]
	response = [('response', amp.Boolean())]

class TransactionChild(child.AMPChild):
	"""
	Even though a transaction child is technically supposed to be asynchronous,
	we're allowing for ampoule calls to be synchronous. This will require a larger
	process pool size, but in return it will allow verbs to continue to be written
	in a synchronous manner, while still meeting all other design goals.
	"""

	def __init__(self):
		self.pool = dbapi.connect(db_url, autocommit=False)
		self.msg_service = messaging.MessageService()
	
	def get_exchange(self, ctx=None):
		if(ctx):
			return exchange.ObjectExchange(self.pool, self.msg_service.get_queue(), ctx)
		else:
			return exchange.ObjectExchange(self.pool)
	
class DefaultTransactionChild(TransactionChild):
	@Authenticate.responder
	def authenticate(self, username, password):
		with self.get_exchange() as x:
			authentication = x.get_verb(1, 'authenticate')
			if(authentication):
				u = authentication(username, password)
				if not(u):
					raise errors.PermissionError("Invalid login credentials. (1)")
				defer.returnValue({'user_id': u.get_id()})
			try:
				u = x.get_object(username)
				if not(u):
					raise errors.PermissionError("Invalid login credentials. (2)")
			except errors.NoSuchObjectError, e:
				raise errors.PermissionError("Invalid login credentials. (3)")
			except errors.AmbiguousObjectError, e:
				raise errors.PermissionError("Invalid login credentials. (4)")
		
			if(u.is_connected_player() and u.is_allowed('multi_login', u)):
				raise errors.PermissionError('User is already logged in.')
		
			if not(x.validate_password(u.get_id(), password)):
				raise errors.PermissionError("Invalid login credentials. (6)")
		return {'user_id': u.get_id()}
	
	@Login.responder
	def login(self, user_id, ip_address):
		print 'user #%s logged in from %s' % (user_id, ip_address)
		
		with self.get_exchange() as x:
			x.login_player(user_id)
			
			system = x.get_object(1)
			if(system.has_verb('connect') and not system.connect(ip_address)):
				raise errors.PermissionError("System connect script denied access.")
			
			user = x.get_object(user_id)
			if(system.has_verb("login")):
				system.login(user)
		
		return {'response': True}
	
	@Logout.responder
	def logout(self, user_id):
		print 'user #%s logged out' % (user_id,)
		
		with self.get_exchange(user_id) as x:
			x.logout_player(user_id)
			
			system = x.get_object(1)
			user = x.get_object(user_id)
			if(system.has_verb("logout")):
				system.logout(user)
		
		return {'response': True}
	
	@Parse.responder
	def parse(self, user_id, sentence):
		with self.get_exchange(user_id) as x:
			caller = x.get_object(user_id)
			
			log.msg('%s: %s' % (caller, sentence))
			parser.parse(caller, sentence)
		
		return {'response': True}
	

