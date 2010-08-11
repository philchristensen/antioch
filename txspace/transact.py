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

from txspace import dbapi, exchange, errors, parser, messaging

__processPool = None
db_url = 'psycopg2://txspace:moavmic7@localhost/txspace'

def get_process_pool():
	global __processPool
	if(__processPool is not None):
		return __processPool
	
	starter = main.ProcessStarter(packages=("twisted", "ampoule"))
	__processPool = pool.ProcessPool(TransactionChild, name='txspace-process-pool', starter=starter)
	
	return __processPool

class WorldTransaction(amp.Command):
	@classmethod
	def run(cls, **kwargs):
		pool = get_process_pool()
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

class DetailObject(WorldTransaction):
	arguments = [
				('user_id', amp.Integer()),
				('lookup_key', amp.String()),
				]
	response = [
				('id', amp.Integer()),
				('name', amp.String()),
				('description', amp.String()),
				('location_id', amp.Integer()),
				('contents', amp.AmpList([
					('name', amp.String()),
					('type', amp.String()),
				])),
				]

class ModifyObject(WorldTransaction):
	arguments = [
				('object_id', amp.Integer()),
				('name', amp.String()),
				('location_id', amp.Integer()),
				('owner_id', amp.Integer()),
				]
	response = [('response', amp.Boolean())]

class CreateObject(WorldTransaction):
	arguments = [
				('name', amp.String()),
				('unique_name', amp.Boolean()),
				('location_id', amp.Integer()),
				('owner_id', amp.Integer()),
				]
	response = [('response', amp.Integer())]

class DeleteObject(WorldTransaction):
	arguments = [
				('object_id', amp.Integer()),
				]
	response = [('response', amp.Boolean())]

class ModifyVerb(WorldTransaction):
	arguments = [
				('verb_id', amp.Integer()),
				('names', amp.ListOf(amp.String())),
				('code', amp.String()),
				('origin_id', amp.Integer()),
				('owner_id', amp.Integer()),
				]
	response = [('response', amp.Boolean())]

class CreateVerb(WorldTransaction):
	arguments = [
				('names', amp.ListOf(amp.String())),
				('code', amp.String()),
				('origin_id', amp.Integer()),
				('owner_id', amp.Integer()),
				]
	response = [('response', amp.Integer())]

class DeleteVerb(WorldTransaction):
	arguments = [
				('verb_id', amp.Integer()),
				]
	response = [('response', amp.Boolean())]

class ModifyProperty(WorldTransaction):
	arguments = [
				('property_id', amp.Integer()),
				('name', amp.String()),
				('value', amp.String()),
				('eval_type_id', amp.Integer()),
				('origin_id', amp.Integer()),
				('owner_id', amp.Integer()),
				]
	response = [('response', amp.Boolean())]

class CreateProperty(WorldTransaction):
	arguments = [
				('name', amp.String()),
				('value', amp.String()),
				('eval_type_id', amp.Integer()),
				('origin_id', amp.Integer()),
				('owner_id', amp.Integer()),
				]
	response = [('response', amp.Integer())]

class DeleteProperty(WorldTransaction):
	arguments = [
				('property_id', amp.Integer()),
				]
	response = [('response', amp.Boolean())]

# class ModifyPermissions(WorldTransaction):
# 	arguments = [
# 				('item_id', amp.Integer()),
# 				('item_type_id', amp.Integer()),
# 				('permissions', amp.ListOf(amp.String())),
# 				]
# 	response = [('response', amp.Boolean())]


class TransactionChild(child.AMPChild):
	"""
	Even though a transaction child is technically supposed to be asynchronous,
	we're allowing for ampoule calls to be synchronous. This will require a larger
	process pool size, but in return it will allow verbs to continue to be written
	in a synchronous manner, while still meeting all other design goals.
	"""

	def __init__(self):
		self.pool = dbapi.connect(db_url)
		self.msg_service = messaging.MessageService()
	
	def get_exchange(self, ctx=None):
		return exchange.ObjectExchange(self.pool, ctx)
	
	@Authenticate.responder
	def authenticate(self, username, password):
		exchange = self.get_exchange()
		
		authentication = exchange.get_verb(1, 'authenticate')
		if(authentication):
			user = authentication(username, password)
			if not(user):
				raise errors.PermissionError("Invalid login credentials. (1)")
			return {'user_id': user.get_id()}
		try:
			user = exchange.get_object(username)
			if not(user):
				raise errors.PermissionError("Invalid login credentials. (2)")
		except errors.NoSuchObjectError, e:
			raise errors.PermissionError("Invalid login credentials. (3)")
		except errors.AmbiguousObjectError, e:
			raise errors.PermissionError("Invalid login credentials. (4)")
		
		if(user.is_connected_player() and user.is_allowed('multi_login', user)):
			raise errors.PermissionError('User is already logged in.')
		
		if not(exchange.validate_password(user.get_id(), password)):
			raise errors.PermissionError("Invalid login credentials. (6)")
		
		exchange.commit()
		return {'user_id': user.get_id()}
	
	@Login.responder
	def login(self, user_id, ip_address):
		print 'user #%s logged in from %s' % (user_id, ip_address)
		
		exchange = self.get_exchange()
		
		exchange.login_player(user_id)
		
		system = exchange.get_object(1)
		if(system.has_verb('connect') and not system.connect(ip_address)):
			raise errors.PermissionError("System connect script denied access.")
		
		user = exchange.get_object(user_id)
		if(system.has_verb("login")):
			system.login(user)
		
		exchange.commit()
		return {'response': True}
	
	@Logout.responder
	def logout(self, user_id):
		print 'user #%s logged out' % (user_id,)
		
		exchange = self.get_exchange(user_id)
		
		exchange.logout_player(user_id)
		
		system = exchange.get_object(1)
		user = exchange.get_object(user_id)
		if(system.has_verb("logout")):
			system.logout(user)
		
		exchange.commit()
		return {'response': True}
	
	@Parse.responder
	@defer.inlineCallbacks
	def parse(self, user_id, sentence):
		exchange = self.get_exchange(user_id)
		messages = self.msg_service.get_queue()
		
		caller = exchange.get_object(user_id)
		
		try:
			log.msg('%s: %s' % (caller, sentence))
			
			l = parser.Lexer(sentence)
			p = parser.TransactionParser(l, caller, exchange, messages)
			
			v = p.get_verb()
			v.execute(p)
		except errors.TestError, e:
			raise e
		except errors.UserError, e:
			messages.send(user_id, dict(
				command		= 'write',
				text		= str(e),
				is_error	= True,
			))
		except Exception, e:
			import traceback
			trace = traceback.format_exc()
			print 'BAD_ERROR: ' + trace
			messages.send(user_id, dict(
				command		= 'write',
				text		= trace,
				is_error	= True,
			))
		
		exchange.commit()
		try:
			yield self.msg_service.connect()
			yield messages.commit()
		except Exception, e:
			print 'ERR: %s' % e
		
		defer.returnValue({'response': True})
	
	@DetailObject.responder
	def detail_object(self, user_id, lookup_key):
		exchange = self.get_exchange(user_id)
		
		obj = exchange.get_object(lookup_key)
		return dict(
			id			= obj.get_id(),
			name		= obj.get_name(),
			location_id	= obj._location_id or 0,
			description	= obj.get('description', 'Nothing much to see here.').value,
			contents	= [],
		)
	
	@ModifyObject.responder
	def modify_object(self, object_id, name, unique_name, owner_id, location_id):
		exchange = self.get_exchange()
		exchange.commit()
		return {'response': None}
	
	@CreateObject.responder
	def create_object(self, name, unique_name, owner_id, location_id):
		exchange = self.get_exchange()
		
		obj = exchange.new(name, unique_name)
		owner = exchange.get_object(owner_id)
		location = exchange.get_object(location_id)
		
		obj.set_owner(owner)
		obj.set_location(location)
		
		exchange.commit()
		return {'response': obj.get_id()}
	
	@DeleteObject.responder
	def delete_object(self, object_id):
		exchange = self.get_exchange()
		exchange.remove(object_id)
		exchange.commit()
		return {'response': True}
	
	@ModifyVerb.responder
	def modify_verb(self, verb_id, **details):
		exchange = self.get_exchange()
		exchange.commit()
		return {'response': None}
	
	@CreateVerb.responder
	def create_verb(self, **details):
		exchange = self.get_exchange()
		exchange.commit()
		return {'response': None}
	
	@DeleteVerb.responder
	def delete_verb(self, verb_id):
		exchange = self.get_exchange()
		exchange.remove('verb', verb_id)
		exchange.commit()
		return {'response': True}
	
	@ModifyProperty.responder
	def modify_property(self, property_id, **details):
		exchange = self.get_exchange()
		exchange.commit()
		return {'response': None}
	
	@CreateProperty.responder
	def create_property(self, **details):
		exchange = self.get_exchange()
		exchange.commit()
		return {'response': None}
	
	@DeleteProperty.responder
	def delete_property(self, property_id, **details):
		exchange = self.get_exchange()
		self.exchange.remove('property', property_id)
		exchange.commit()
		return {'response': True}
	
	# @ModifyPermissions.responder
	# def modify_permissions(self, item_id, item_type_id, permissions):
	# 	pass
