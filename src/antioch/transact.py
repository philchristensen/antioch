# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Execution layer
"""

import simplejson, time

from twisted.python import log
from twisted.internet import defer
from twisted.protocols import amp

from ampoule import child, pool, main, util

from antioch import dbapi, exchange, errors, parser, messaging, sql, code, modules

__processPools = {}
default_db_url = 'psycopg2://antioch:moavmic7@localhost/antioch'
code_timeout = 5

profile_transactions = False

def get_process_pool(child=None, *args):
	if(child is None):
		child = DefaultTransactionChild
	
	global __processPools
	if(child.__name__ in __processPools):
		return __processPools[child.__name__]
	
	starter = main.ProcessStarter(packages=("twisted", "ampoule", "antioch"))
	__processPools[child.__name__] = pool.ProcessPool(child, name='antioch-process-pool', starter=starter, ampChildArgs=args)
	
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
	def run(cls, transaction_child=None, db_url='', **kwargs):
		if(db_url):
			pool = get_process_pool(transaction_child, db_url)
		else:
			pool = get_process_pool(transaction_child)
		return pool.doWork(cls, _timeout=code_timeout, **kwargs)

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

class RegisterTask(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('delay', amp.Integer()),
		('origin_id', amp.String()),
		('verb_name', amp.String()),
		('args', amp.String()),
		('kwargs', amp.String()),
	]
	response = [('task_id', amp.Integer())]

class RunTask(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('task_id', amp.Integer()),
	]
	response = [('response', amp.Boolean())]

class IterateTasks(WorldTransaction):
	arguments = [
	]
	response = [('response', amp.Boolean())]

class TransactionChild(child.AMPChild):
	"""
	Even though a transaction child is technically supposed to be asynchronous,
	we're allowing for ampoule calls to be synchronous. This will require a larger
	process pool size, but in return it will allow verbs to continue to be written
	in a synchronous manner, while still meeting all other design goals.
	"""

	def __init__(self, db_url=''):
		if not(db_url):
			db_url = default_db_url
		
		t = time.time()
		self.pool = dbapi.connect(db_url, autocommit=False)
		if(profile_transactions):
			print "[transact] db connection took %s seconds" % (time.time() - t)
		
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
	
			if not(u.validate_password(password)):
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
	
	@RegisterTask.responder
	def register_task(self, user_id, delay, origin_id, verb_name, args, kwargs):
		with self.get_exchange(user_id) as x:
			task_id = x.register_task(user_id, delay, origin_id, verb_name, args, kwargs)
		return {'task_id': task_id}
	
	@RunTask.responder
	def run_task(self, user_id, task_id):
		with self.get_exchange(user_id) as x:
			task = x.get_task(task_id)
			if(not task or task['killed']):
				return {'response': False}
			
			origin = x.get_object(task['origin_id'])
			args = simplejson.loads(task['args'])
			kwargs = simplejson.loads(task['kwargs'])
			
			v = origin.get_verb(task['verb_name'])
			v(*args, **kwargs)
		
		return {'response': True}
	
	@IterateTasks.responder
	def iterate_tasks(self):
		# note this is a 'superuser exchange'
		# should be fine, since all iterate_task does
		# is create another subprocess for the proper user
		with self.get_exchange() as x:
			return {'response': x.iterate_task(self)}
