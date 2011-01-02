# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Isolate verb code into individual subprocesses
"""

from __future__ import with_statement

import time

from twisted.python import log
from twisted.internet import defer
from twisted.protocols import amp

from ampoule import child, pool, main, util

from antioch import dbapi, exchange, errors, parser, messaging, sql, code, modules, json

__processPools = {}
default_db_url = 'psycopg2://antioch:moavmic7@localhost/antioch'
job_timeout = 3

profile_transactions = False

def get_process_pool(child=None, *args):
	"""
	Get the process pool belonging to the specified child.
	
	Optionally pass a custom TransactionChild 
	Optionally pass additional args to the TransactionChild
	"""
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
	"""
	Shutdown the process pool.
	"""
	if(child is None):
		child = DefaultTransactionChild
	
	global __processPools
	if(child.__name__ in __processPools):
		yield __processPools[child.__name__].stop()
		del __processPools[child.__name__]

class WorldTransaction(amp.Command):
	"""
	All amp.Commands used in antioch can find their own process pool.
	"""
	errors = {
		errors.AccessError : 'ACCESS_ERROR',
		errors.PermissionError : 'PERMISSION_ERROR',
	}
	
	@classmethod
	def run(cls, transaction_child=None, db_url='', **kwargs):
		if(db_url):
			pool = get_process_pool(transaction_child, db_url)
		else:
			pool = get_process_pool(transaction_child)
		d = pool.doWork(cls, _timeout=job_timeout, **kwargs)
		d.addErrback(log.err)
		return d

class Authenticate(WorldTransaction):
	"""
	Return the user id for the username/password combo, if valid.
	"""
	arguments = [
		('username', amp.String()),
		('password', amp.String()),
		('ip_address', amp.String()),
	]
	response = [
		('user_id', amp.Integer()),
	]

class Login(WorldTransaction):
	"""
	Register a login for the provided user_id.
	"""
	arguments = [
		('user_id', amp.Integer()),
		('session_id', amp.String()),
		('ip_address', amp.String()),
	]
	response = [('response', amp.Boolean())]

class Logout(WorldTransaction):
	"""
	Register a logout for the provided user_id.
	"""
	arguments = [
		('user_id', amp.Integer()),
	]
	response = [('response', amp.Boolean())]

class Parse(WorldTransaction):
	"""
	Parse a command sentence for the provided user_id.
	"""
	arguments = [
		('user_id', amp.Integer()),
		('sentence', amp.String()),
	]
	response = [('response', amp.Boolean())]

class RegisterTask(WorldTransaction):
	"""
	Register a delayed task for the provided user_id.
	"""
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
	"""
	Run a task for a particular user.
	"""
	arguments = [
		('user_id', amp.Integer()),
		('task_id', amp.Integer()),
	]
	response = [('response', amp.Boolean())]

class IterateTasks(WorldTransaction):
	"""
	Run one waiting task, if possible.
	"""
	arguments = [
	]
	response = [('response', amp.Boolean())]

class TransactionChild(child.AMPChild):
	"""
	Handle transactions for the game server.
	
	Even though a transaction child is technically supposed to be asynchronous,
	we're allowing for ampoule calls to be synchronous. This will require a larger
	process pool size, but in return it will allow verbs to continue to be written
	in a synchronous manner, while still meeting all other design goals.
	"""
	def __init__(self, db_url=''):
		"""
		Create a new TransactionChild.
		
		Optionally supply db_url to specify the database to connect to.
		"""
		if not(db_url):
			db_url = default_db_url
		
		t = time.time()
		self.pool = dbapi.connect(db_url, autocommit=False)
		if(profile_transactions):
			print "[transact] db connection took %s seconds" % (time.time() - t)
		
		self.msg_service = messaging.MessageService()
	
	def get_exchange(self, ctx=None):
		"""
		Get an ObjectExchange instance for the provided context.
		"""
		if(ctx):
			return exchange.ObjectExchange(self.pool, self.msg_service.get_queue(), ctx)
		else:
			return exchange.ObjectExchange(self.pool)
	
class DefaultTransactionChild(TransactionChild):
	"""
	Provide fundamental antioch transaction methods.
	"""
	@Authenticate.responder
	def authenticate(self, username, password, ip_address):
		"""
		Return the user id for the username/password combo, if valid.
		"""
		with self.get_exchange() as x:
			connect = x.get_verb(1, 'connect')
			if(connect):
				connect(ip_address)
			
			authentication = x.get_verb(1, 'authenticate')
			if(authentication):
				u = authentication(username, password, ip_address)
				if(u):
					return {'user_id': u.get_id()}
			try:
				u = x.get_object(username)
				if not(u):
					raise errors.PermissionError("Invalid login credentials. (2)")
			except errors.NoSuchObjectError, e:
				raise errors.PermissionError("Invalid login credentials. (3)")
			except errors.AmbiguousObjectError, e:
				raise errors.PermissionError("Invalid login credentials. (4)")
			
			multilogin_accounts = x.get_property(1, 'multilogin_accounts')
			if(u.is_connected_player()):
				if(not multilogin_accounts or u not in multilogin_accounts.value):
					raise errors.PermissionError('User is already logged in.')

			if not(u.validate_password(password)):
				raise errors.PermissionError("Invalid login credentials. (6)")
		return {'user_id': u.get_id()}
	
	@Login.responder
	def login(self, user_id, session_id, ip_address):
		"""
		Register a login for the provided user_id.
		"""
		with self.get_exchange(user_id) as x:
			x.login_player(user_id, session_id)
			
			system = x.get_object(1)
			if(system.has_verb("login")):
				system.login()
		
		print 'user #%s logged in from %s' % (user_id, ip_address)
		return {'response': True}
	
	@Logout.responder
	def logout(self, user_id):
		"""
		Register a logout for the provided user_id.
		"""
		# we want to make sure to logout the user even
		# if the logout verb fails
		with self.get_exchange(user_id) as x:
			x.logout_player(user_id)
		
		with self.get_exchange(user_id) as x:
			system = x.get_object(1)
			if(system.has_verb("logout")):
				system.logout()
		
		print 'user #%s logged out' % (user_id,)
		return {'response': True}
	
	@Parse.responder
	def parse(self, user_id, sentence):
		"""
		Parse a command sentence for the provided user_id.
		"""
		with self.get_exchange(user_id) as x:
			caller = x.get_object(user_id)
			
			log.msg('%s: %s' % (caller, sentence))
			parser.parse(caller, sentence)
		return {'response': True}
	
	@RegisterTask.responder
	def register_task(self, user_id, delay, origin_id, verb_name, args, kwargs):
		"""
		Register a delayed task for the provided user_id.
		"""
		with self.get_exchange(user_id) as x:
			task_id = x.register_task(user_id, delay, origin_id, verb_name, args, kwargs)
		return {'task_id': task_id}
	
	@RunTask.responder
	def run_task(self, user_id, task_id):
		"""
		Run a task for a particular user.
		"""
		with self.get_exchange(user_id) as x:
			task = x.get_task(task_id)
			if(not task or task['killed']):
				return {'response': False}
			
			origin = x.get_object(task['origin_id'])
			args = json.loads(task['args'])
			kwargs = json.loads(task['kwargs'])
			
			v = origin.get_verb(task['verb_name'])
			v(*args, **kwargs)
		
		return {'response': True}
	
	@IterateTasks.responder
	def iterate_tasks(self):
		"""
		Run one waiting task, if possible.
		"""
		# note this is a 'superuser exchange'
		# should be fine, since all iterate_task does
		# is create another subprocess for the proper user
		with self.get_exchange() as x:
			return {'response': x.iterate_task(self)}
