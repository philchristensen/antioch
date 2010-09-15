"""
The primary change brought about by the change to using a relational database is
that the objects handled by system- and user-verbs are no longer the actual
objects of the system. The database records are now the actual objects, and
these classes now just a window into the database.

Because verbs will run inside their own transaction, we don't have to worry
about another process/user changing the database during the course of a verb.
However, there's always the possibility of doing something like:

	verbs = o.get_verbs()
	verbs2 = o.get_verbs()
	
	verbs[0].name = 'new name'
	verbs[1].code = 'caller.write("hello")'

This sample code omits any 'saving' step, which may or may not be possible, but
the end question is the same. One possible solution to this in this case is that
before a resulting object is passed to the user code, it could pass through a
filter that returns a cached copy of the existing object. Some kind of
weak references-based dictionary keyed on object ID would be sufficient.
"""

from txspace import errors, code

default_permissions = (
	'anything',
	'read',
	'write',
	'entrust',
	'execute',
	'move',
	'transmute',
	'derive',
	'develop',
)

class PropertyStub(object):
	def __init__(self, value):
		self.value = value	

class Entity(object):
	def __repr__(self):
		return '<%s>' % (self)
	
	def set_id(self, id):
		if(self._id != 0):
			raise RuntimeError("Can't redefine a %s's ID." % self.get_type())
		self._id = id
	
	def get_id(self):
		return self._id
	
	id = property(get_id)
	
	def get_origin(self):
		if(self.get_type() == 'object'):
			return self
		
		self.check('read', self)
		return self._ex.instantiate('object', id=self._origin_id)
	
	origin = property(get_origin)
	
	def get_exchange(self):
		return self._ex
	
	def get_context(self):
		return self._ex.get_context()
	
	def save(self):
		self._ex.save(self)
	
	def destroy(self):
		self.check('destroy', self)
		self._ex.destroy(self)
	
	def set_owner(self, owner):
		self.check('entrust', self)
		self._owner_id = owner.get_id()
		self.save()
	
	def get_owner(self):
		#self.check('read', self)
		if not(self._owner_id):
			return None
		return self.get_exchange().instantiate('object', id=self._owner_id)
	
	owner = property(get_owner, set_owner)

	def check(self, permission, subject):
		ctx = self.get_context()
		if ctx and not(ctx.is_allowed(permission, subject)):
			raise errors.AccessError(ctx, permission, subject)
	
	def allow(self, accessor, permission, create=False):
		if(isinstance(accessor, Object)):
			self._ex.allow(self, accessor.get_id(), permission, create)
		else:
			self._ex.allow(self, accessor, permission, create)
	
	def deny(self, accessor, permission, create=False):
		if(isinstance(accessor, Object)):
			self._ex.deny(self, accessor.get_id(), permission, create)
		else:
			self._ex.deny(self, accessor, permission, create)
	
	def get_type(self):
		return type(self).__name__.lower()

class Object(Entity):
	def __init__(self, exchange):
		self._id = 0
		self._ex = exchange
		
		self._name = ''
		self._unique_name = False
		self._owner_id = None
		self._location_id = None
	
	def __str__(self):
		"""
		Return a string representation of this class. These take the form
		of "#0 (System Object)"; the object ID is prefixed by a pound sign,
		and the ID is followed by the real name of the object in parentheses.
		"""
		return "#%s (%s)" % (self._id, self._name)
	
	def __getattr__(self, name):
		# used for verbs
		v = self.get_verb(name)
		if(v is None):
			raise errors.NoSuchVerbError("No such verb `%s` on %s" % (name, self))
		return v
	
	def get_details(self):
		return dict(
			id			= self._id,
			kind		= self.get_type(),
			name		= self._name,
			parents 	= ', '.join([str(x) for x in self.get_parents()]),
			owner		= str(self.get_owner()),
			location	= str(self.get_location()),
			verbs		= self._ex.get_verb_list(self.get_id()),
			properties	= self._ex.get_property_list(self.get_id()),
		)
	
	def owns(self, subject):
		return subject.get_owner() == self
	
	def get_verb(self, name, recurse=True):
		# self.check('read', self)
		v = self._ex.get_verb(self._id, name, recurse=recurse)
		return v
	
	def add_verb(self, name):
		self.check('write', self)
		ctx = self._ex.get_context()
		owner_id = ctx.get_id() if ctx else None
		
		v = self._ex.instantiate('verb', origin_id=self._id, owner_id=owner_id)
		v.add_name(name)
		return v
	
	def remove_verb(self, name):
		self.check('write', self)
		self._ex.remove_verb(origin_id=self._id, name=name)
	
	def has_verb(self, name):
		return self._ex.has(self._id, 'verb', name)
	
	def has_callable_verb(self, name):
		return self._ex.has(self._id, 'verb', name, unrestricted=False)
	
	def get(self, name, default=None):
		try:
			return self[name]
		except errors.NoSuchPropertyError, e:
			return PropertyStub(default)
	
	def get_ancestor_with(self, type, name):
		return self._ex.get_ancestor_with(self._id, type, name)
	
	def __getitem__(self, name):
		if(isinstance(name, (int, long))):
			raise IndexError(name)
		# used for properties
		p = self.get_property(name)
		if(p is None):
			raise errors.NoSuchPropertyError(name, self)
		return p
	
	def __contains__(self, name):
		return self.has_readable_property(name)
	
	def get_property(self, name, recurse=True):
		# self.check('read', self)
		p = self._ex.get_property(self._id, name, recurse=recurse)
		# if(p is not None and p.origin != self):
		# 	return self.check('inherit', p)
		return p
	
	def add_property(self, name):
		self.check('write', self)
		ctx = self._ex.get_context()
		owner_id = ctx.get_id() if ctx else None
		p = self._ex.instantiate('property', origin_id=self._id, name=name, owner_id=owner_id)
		return p
	
	def remove_property(self, name):
		self.check('write', self)
		self._ex.remove_property(origin_id=self._id, name=name)
	
	def has_property(self, name):
		return self._ex.has(self._id, 'property', name)
	
	def has_readable_property(self, name):
		return self._ex.has(self._id, 'property', name, unrestricted=False)
	
	def is_player(self):
		return self._ex.is_player(self.get_id())
	
	def set_player(self, is_player, is_wizard=False, passwd=None):
		return self._ex.set_player(self.get_id(), is_player, is_wizard, passwd)
	
	def is_connected_player(self):
		return self._ex.is_connected_player(self.get_id())
	
	def set_name(self, name, real=False):
		self.check('write', self)
		if(real):
			if(self._name != name and self._ex.is_unique_name(name)):
				raise ValueError("Sorry, '%s' is a reserved name." % name)
			elif(self._unique_name and self._ex.refs(name) > 1):
				raise ValueError("Sorry, '%s' is an ambiguous name." % name)
			
			self._name = name
			self.save()
		else:
			if('name' in self):
				self['name'].value = name
			else:
				p = self.add_property('name')
				p.value = name
	
	def get_name(self, real=False):
		self.check('read', self)
		if(real or 'name' not in self):
			return self._name
		else:
			return self['name'].value
	
	def find(self, name):
		return self._ex.find(self.get_id(), name)
	
	def contains(self, subject, recurse=True):
		return self._ex.contains(self.get_id(), subject.get_id(), recurse)
	
	def get_contents(self):
		return self._ex.get_contents(self.get_id())
	
	def set_location(self, location):
		self.check('move', self)
		if(location and self.contains(location)):
			raise errors.RecursiveError("Sorry, '%s' already contains '%s'" % (self, location))
		self._location_id = location.get_id() if location else None
		self.save()
	
	def get_location(self):
		self.check('read', self)
		if not(self._location_id):
			return None
		return self._ex.instantiate('object', id=self._location_id)
	
	def has_parent(self, parent):
		return self._ex.has_parent(self.get_id(), parent.get_id())
	
	def get_parents(self, recurse=False):
		self.check('read', self)
		return self._ex.get_parents(self._id, recurse)
	
	def remove_parent(self, parent):
		self.check('transmute', self)
		self._ex.remove_parent(parent.get_id(), self.get_id())
	
	def add_parent(self, parent):
		self.check('transmute', self)
		self.check('derive', parent)
		
		if(parent.has_parent(self)):
			raise errors.RecursiveError("Sorry, '%s' is already parent to '%s'" % (self, parent))
		self._ex.add_parent(self.get_id(), parent.get_id())
	
	def is_allowed(self, permission, subject):
		return self._ex.is_allowed(self, permission, subject)
	
	name = property(get_name, set_name)
	location = property(get_location, set_location)

class Verb(Entity):
	def __init__(self, origin):
		"""
		Create a verb record and attach it to object.
		"""
		self._id = 0
		self._origin_id = origin.get_id()
		self._ex = origin.get_exchange()
		
		self._code = ''
		self._owner_id = None
		self._ability = False
		self._method = False
	
	def __call__(self, *args, **kwargs):
		if not(self._method):
			raise RuntimeError("%s is not a method." % self)
		self.check('execute', self)
		
		from txspace import parser
		default_parser = parser.TransactionParser(parser.Lexer(''), self._ex.get_context(), self._ex)
		env = code.get_environment(default_parser)
		env['args'] = args
		env['kwargs'] = kwargs
		return code.r_exec(self._code, env)
	
	def __str__(self):
		"""
		Return a string representation of this class.
		"""
		return "%s #%s on %s" % (
			[['Verb', 'Ability'][self._ability], 'Method'][self._method], self._id, self.origin
		)
	
	def get_details(self):
		return dict(
			id			= self.get_id(),
			kind		= self.get_type(),
			exec_type	= 'verb' if not self._method else 'method' if not self._ability else 'ability',
			owner		= str(self.get_owner()),
			names		= self.get_names(),
			code		= str(self.get_code()),
			origin		= str(self.get_origin()),
		)
	
	def execute(self, parser):
		self.check('execute', self)
		
		env = code.get_environment(parser)
		code.r_exec(self._code, env)
	
	def add_name(self, name):
		self.check('write', self)
		return self._ex.add_verb_name(self.get_id(), name)
	
	def remove_name(self, name):
		self.check('write', self)
		return self._ex.remove_verb_name(self.get_id(), name)
	
	def get_names(self):
		# self.check('read', self)
		return self._ex.get_verb_names(self.get_id())
	
	def set_names(self, given_names):
		old_names = self.get_names()
		[self.remove_name(n) for n in old_names if n not in given_names]
		[self.add_name(n) for n in given_names if n not in old_names]
	
	def set_code(self, code):
		self.check('develop', self)
		self._code = code
		self.save()
	
	def get_code(self):
		self.check('read', self)
		return self._code
	
	def set_ability(self, ability):
		self.check('develop', self)
		self._ability = bool(ability)
		self.save()
	
	def is_ability(self):
		# self.check('read', self)
		return self._ability
	
	def set_method(self, method):
		self.check('develop', self)
		self._method = bool(method)
		self.save()
	
	def is_method(self):
		# self.check('read', self)
		return self._method
	
	def is_executable(self):
		try:
			self.check('execute', self)
		except errors.PermissionError, e:
			return False
		return True
	
	def performable_by(self, caller):
		if(self.is_method()):
			return False
		if not(caller.is_allowed('execute', self)):
			return False
		elif(self.is_ability()):
			return caller is self.origin or caller.has_parent(self.origin)
		return False
	
	name = property(lambda x: x.get_names().pop(0))
	names = property(get_names)
	code = property(get_code, set_code)
	ability = property(is_ability, set_ability)
	method = property(is_method, set_method)
	executable = property(is_executable)

class Property(Entity):
	def __init__(self, origin):
		"""
		Create a property record and attach it to object.
		"""
		self._id = 0
		self._origin_id = origin.get_id()
		self._ex = origin.get_exchange()
		
		self._name = ''
		self._value = None
		self._type = 'string'
		self._owner_id = None
	
	def __str__(self):
		"""
		Return a string representation of this class.
		"""
		return 'property #%s (%s) on %s' % (self._id, self._name, self.origin)
	
	def get_details(self):
		return dict(
			id			= self.get_id(),
			kind		= self.get_type(),
			owner		= str(self.get_owner()),
			name		= self.get_name(),
			value		= str(self._value),
			type		= str(self._type),
			origin		= str(self.get_origin()),
		)
	
	def is_readable(self):
		try:
			self.check('read', self)
		except errors.PermissionError, e:
			return False
		return True
	
	def set_name(self, name):
		self.check('write', self)
		self._name = name
		self.save()
	
	def get_name(self):
		self.check('read', self)
		return self._name
	
	def set_value(self, value, type='string'):
		self.check('write', self)
		if(type == 'dynamic'):
			raise RuntimeError('Dynamic properties not available yet.')
		self._value = value
		self._type = type
		self.save()
	
	def get_value(self):
		self.check('read', self)
		return self._value
	
	value = property(get_value, set_value)
	name = property(get_name, set_name)
	readable = property(is_readable)
