# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Code


Various methods to run and populate the environment of
'untrusted' code.
"""

import traceback, warnings

from twisted.internet import defer

from txspace import errors, security
from txspace.security import Q

def r_eval(code, environment):
	if not(environment):
		raise RuntimeError('No environment')
	return eval(code, environment)

def r_exec(code, environment):
	if not(environment):
		raise RuntimeError('No environment')
	exec(code, environment)
	if("__result__" in environment):
		return environment["__result__"]

def context_filter(value, registry=None, ctx=None):
	from txspace import entity, prop, verb
	found_entity = False
	found_ctx = False
	if(isinstance(value, EntityContext)):
		if(registry is None):
			raise RuntimeError("Can't filter context without a registry.")
		if(found_entity):
			raise RuntimeError("Found a mix of entities and contexts.")
		found_ctx = True
		result = registry.get(value.get_id())
	elif(isinstance(value, entity.Entity)):
		if(ctx is False):
			raise RuntimeError("Can't filter entity without a context.")
		if(found_ctx):
			raise RuntimeError("Found a mix of entities and contexts.")
		found_entity = True
		result = EntityContext(ctx, value)
	elif(isinstance(value, (prop.Property, verb.Verb))):
		result = value
	elif(isinstance(value, Exception)):
		result = value
	elif(isinstance(value, dict)):
		result = {}
		for k, v in value.items():
			result[k] = context_filter(v, registry=registry, ctx=ctx)
	elif(isinstance(value, (tuple, list))):
		result = []
		for i in range(len(value)):
			result.append(context_filter(value[i], registry=registry, ctx=ctx))
	elif(isinstance(value, (int, long, float, str, unicode, bool))):
		result = value
	#pass functions, methods and classes
	elif(callable(value)):
		result = value
	elif(value is None):
		result = value
	else:
		raise RuntimeError("Objects of type %s are not supported (%r)." % (type(value), value))
		#warnings.warn("Objects of type %s are not supported (%r)." % (type(value), value))
		result = value
	
	return result

def noncontextual(ctx, registry):
	"""
	A decorator for functions called by verb code.
	
	It will automagically replace EntityContext objects with real Entities
	so that support code doesn't need to deal with contexts.
	"""
	def _func(func):
		def __func(*args, **kwargs):
			args, kwargs = context_filter((args, kwargs), registry=registry)
			result = func(*args, **kwargs)
			if(isinstance(result, defer.Deferred)):
				return result
			return context_filter(result, ctx=ctx)
		return __func
	return _func

def user_errback(user):
	"""
	A decorator to ensure that user errbacks from verb code are written to the user that caused them.
	"""
	def _errback(failure):
		if(user.is_connected_player(Q)):
			if(isinstance(failure.value, errors.UserError)):
				user.write(user, str(failure.value), is_error=True)
			else:
				trace = traceback.format_exc()
				user.write(user, trace, is_error=True)
	
	def _errback_wrapper(func):
		def _func(*args, **kwargs):
			d = func(*args, **kwargs)
			d.addErrback(_errback)
			return True
		return _func
	
	return _errback_wrapper

def get_environment(ctx, verb, parser, extra={}):
	"""
	Get a dictionary object, suitable for passing to eval()/exec(),
	which contains the environment that verbs will be run in.
	"""
	from txspace import entity, security, editors
	
	result = parser.get_details()
	caller = result.get('caller')
	registry = parser.registry
	
	@user_errback(ctx)
	@noncontextual(ctx, registry)
	def _edit_verb(*args, **kwargs):
		return editors.edit_verb(*args, **kwargs)
	
	@user_errback(ctx)
	@noncontextual(ctx, registry)
	def _edit_property(*args, **kwargs):
		return editors.edit_property(*args, **kwargs)
	
	@user_errback(ctx)
	@noncontextual(ctx, registry)
	def _edit_acl(*args, **kwargs):
		return editors.edit_acl(*args, **kwargs)
	
	@user_errback(ctx)
	@noncontextual(ctx, registry)
	def _edit_entity(*args, **kwargs):
		return editors.edit_entity(*args, **kwargs)
	
	@user_errback(ctx)
	def _logout():
		return caller._connection.logout()
	
	def _new_obj(name, unique=False):
		system = registry.get(0)
		can_create = False
		if(system.has_callable_verb(Q, 'approve_creation')):
			can_create = system.call_verb(Q, 'approve_creation', name, parser.caller)
		
		if(can_create or caller.is_programmer(ctx)):
			obj = registry.new(name, unique)
			obj.set_owner(Q, caller)
			result = EntityContext(ctx, obj)
			
			if(system.has_callable_verb(Q, 'post_creation')):
				system.call_verb(Q, 'post_creation', name, parser.caller)
			
			return result
		else:
			raise errors.PermissionError, "You are not allowed to create new objects."
	
	@noncontextual(ctx, registry)
	def _allow(accessor, access_str, subject):
		if not(caller.owns(Q, subject)):
			errors.PermissionError('You are not allowed to set permissions on %s' % subject)
		security.allow(accessor, access_str, subject)
	
	@noncontextual(ctx, registry)
	def _deny(accessor, access_str, subject):
		if not(caller.owns(Q, subject)):
			errors.PermissionError('You are not allowed to set permissions on %s' % subject)
		security.deny(accessor, access_str, subject)
	
	result.update(extra)
	
	result.update(dict(
		system			= registry.get(0),
		here			= caller.get_location(ctx),
		
		edit_verb		= _edit_verb,
		edit_property	= _edit_property,
		edit_acl		= _edit_acl,
		edit_entity		= _edit_entity,
		
		logout			= _logout,
		
		allow			= _allow,
		deny			= _deny,
		
		new_obj			= _new_obj,
		get_obj			= noncontextual(ctx, registry)(registry.get),
		count_names 	= registry.refs,
		
		get_dobj		= noncontextual(ctx, registry)(parser.get_dobj),
		get_dobj_str	= parser.get_dobj_str,
		has_dobj		= parser.has_dobj,
		has_dobj_str	= parser.has_dobj_str,
		
		get_pobj		= noncontextual(ctx, registry)(parser.get_pobj),
		get_pobj_str 	= parser.get_pobj_str,
		has_pobj 		= parser.has_pobj,
		has_pobj_str 	= parser.has_pobj_str,
	))
	
	result = context_filter(result, ctx=ctx)
	
	if(caller.is_wizard(Q)):
		result['load_verb'] = registry.load_verb
		result['reload_verb'] = registry.reload_verb
		result['registry'] = registry

	for name, value in errors.__dict__.items():
		if(name.endswith('Error')):
			result[name] = value
	
	for name, value in security.__dict__.items():
		if(callable(value) and getattr(value, 'exposed', False)):
			result[name] = noncontextual(ctx, registry)(value)
	
	return result

class EntityContext(object):
	def __init__(self, context, obj):
		self.context = context
		self.obj = obj
	
	def __getattribute__(self, name):
		obj = super(EntityContext, self).__getattribute__('obj')
		context = super(EntityContext, self).__getattribute__('context')
		
		attrib = getattr(obj, name)
		if(callable(attrib)):
			if(attrib.func_name.startswith('__')):
				return attrib
			def _result(*args, **kwargs):
				args = context_filter(args, registry=obj.get_registry(Q))
				kwargs = context_filter(kwargs, registry=obj.get_registry(Q))
				result = attrib(context, *args, **kwargs)
				return context_filter(result, ctx=context)
			return _result
		raise AttributeError(name)
	
	def __add__(self, other):
		"""
		Treat this as a string when added to things.
		"""
		return str(self) + other
	
	def __radd__(self, other):
		"""
		Treat this as a string when added to things.
		"""
		return other + str(self)
	
	def __str__(self):
		obj = super(EntityContext, self).__getattribute__('obj')
		return str(obj)
	
	def __repr__(self):
		obj = super(EntityContext, self).__getattribute__('obj')
		return repr(obj)

