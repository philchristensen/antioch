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

from txspace import dbapi, exchange, errors, parser, messaging, sql, code

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

class GetObjectDetails(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
	]
	response = [
		('id', amp.Integer()),
		('name', amp.String()),
		('kind', amp.String()),
		('parents', amp.String()),
		('owner', amp.String()),
		('location', amp.String()),
		('properties', amp.AmpList([
			('id', amp.Integer()),
			('name', amp.String()),
		])),
		('verbs', amp.AmpList([
			('id', amp.Integer()),
			('names', amp.String()),
		])),
	]

class OpenEditor(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('type', amp.String()),
		('name', amp.String()),
	]

class OpenAccess(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('type', amp.String()),
		('name', amp.String()),
	]

class ModifyObject(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.Integer()),
		('name', amp.String()),
		('location', amp.String()),
		('parents', amp.String()),
		('owner', amp.String()),
	]

class ModifyVerb(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('verb_id', amp.String()),
		('names', amp.String()),
		('code', amp.String()),
		('exec_type', amp.String()),
		('owner', amp.String()),
	]

class ModifyProperty(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('property_id', amp.String()),
		('name', amp.String()),
		('value', amp.String()),
		('type', amp.String()),
		('owner', amp.String()),
	]

class ModifyAccess(WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('type', amp.String()),
		('access', amp.AmpList([
			('access_id', amp.Integer()),
			('deleted', amp.Boolean()),
			('rule', amp.String()),
			('access', amp.String()),
			('accessor', amp.String()),
			('permission', amp.String()),
			('weight', amp.Integer()),
		])),
	]

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
		return exchange.ObjectExchange(self.pool, self.msg_service.get_queue(), ctx)
	
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
			
			try:
				log.msg('%s: %s' % (caller, sentence))
				parser.parse(caller, sentence)
			except errors.TestError, e:
				raise e
			except errors.UserError, e:
				x.queue.send(user_id, dict(
					command		= 'write',
					text		= str(e),
					is_error	= True,
				))
			except Exception, e:
				import traceback
				trace = traceback.format_exc()
				print 'BAD_ERROR: ' + trace
				x.queue.send(user_id, dict(
					command		= 'write',
					text		= trace,
					is_error	= True,
				))
		
		return {'response': True}
	
	@OpenEditor.responder
	def open_editor(self, user_id, object_id, type, name):
		with self.get_exchange(user_id) as x:
			if(type == 'object'):
				item = x.get_object(object_id)
			else:
				item = getattr(x, 'get_' + type)(object_id, name)
				if(item is None):
					item = x.instantiate(type, owner_id=user_id, origin_id=object_id, name=name)
					if(type == 'verb'):
						item.add_name(name)
			caller = x.get_object(user_id)
			p = parser.TransactionParser(parser.Lexer(''), caller, x)
			code.edit(p)(item)
		
		return {'response': True}
	
	@OpenAccess.responder
	def open_access(self, user_id, object_id, type, name):
		with self.get_exchange(user_id) as x:
			origin = x.get_object(object_id)
			caller = x.get_object(user_id)
			if(type == 'object'):
				item = origin
			else:
				item = getattr(origin, 'get_' + type)(name)
			
			p = parser.TransactionParser(parser.Lexer(''), caller, x)
			code.access(p)(item)
		
		return {'response': True}
	
	@ModifyObject.responder
	def modify_object(self, user_id, object_id, name, location, parents, owner):
		with self.get_exchange(user_id) as x:
			o = x.get_object(object_id)
			o.set_name(name, real=True)
			o.set_location(x.get_object(location))
			o.set_owner(x.get_object(owner))
			
			old_parents = o.get_parents()
			new_parents = [x.get_object(p.strip()) for p in parents.split(',') if p.strip()]
			
			[o.remove_parent(p) for p in old_parents if p not in new_parents]
			[o.add_parent(p) for p in new_parents if p not in old_parents]
		
		return {'response': True}
	
	@ModifyVerb.responder
	def modify_verb(self, user_id, object_id, verb_id, names, code, exec_type, owner):
		with self.get_exchange(user_id) as x:
			names = [n.strip() for n in names.split(',')]
			
			v = x.get_verb(exchange.extract_id(object_id), names[0])
			v.set_names(names)
			v.set_owner(x.get_object(owner))
			v.set_code(code)
			
			if(exec_type == 'ability'):
				v.set_ability(True)
				v.set_method(False)
			elif(exec_type == 'method'):
				v.set_ability(False)
				v.set_method(True)
			else:
				v.set_ability(False)
				v.set_method(False)
		
		return {'response': True}

	@ModifyProperty.responder
	def modify_property(self, user_id, object_id, property_id, name, value, type, owner):
		with self.get_exchange(user_id) as x:
			p = x.get_property(exchange.extract_id(object_id), name)
			p.set_name(name)
			p.set_owner(x.get_object(owner))
			p.set_value(value, type=type)
		
		return {'response': True}

	@ModifyAccess.responder
	def modify_access(self, user_id, object_id, type, access):
		with self.get_exchange(user_id) as x:
			subject = x.get_object(object_id)
			for rule in access:
				if(rule['access'] == 'accessor'):
					rule['accessor'] = x.get_object(rule['accessor'])
				x.update_access(subject=subject, **rule)
		
		return {'response': True}
	
	@GetObjectDetails.responder
	def get_object_details(self, user_id, object_id):
		with self.get_exchange(user_id) as x:
			obj = x.get_object(object_id)
			return obj.get_details()
