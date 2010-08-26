# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Code
"""
from txspace import errors

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

def api(func):
	def _api(p):
		def __api(*args, **kwargs):
			return func(p, *args, **kwargs)
		return __api
	
	api.locals = getattr(api, 'locals', {})
	api.locals[func.func_name] = _api
	
	return _api

@api
def write(p, user, text, is_error=False):
	#print 'trying to write: ' + str(text)
	p.exchange.queue.send(user.get_id(), dict(
		command		= 'write',
		text		= str(text),
		is_error	= is_error,
	))

@api
def observe(p, user, observations):
	#print 'trying to display: ' + str(observations)
	p.exchange.queue.send(user.get_id(), dict(
		command			= 'observe',
		observations	= observations,
	))

@api
def edit(p, item):
	details = dict(
		id			= item.get_id(),
		kind		= item.get_type(),
		owner		= str(item.get_owner()),
	)
	
	if(details['kind'] == 'object'):
		details['name'] = item.get_name(real=True)
		details['location'] = str(item.get_location())
		details['parents'] = ', '.join([str(x) for x in item.get_parents()])
		details['verbs'] = p.exchange.get_verb_list(item.get_id())
		details['properties'] = p.exchange.get_property_list(item.get_id())
	elif(details['kind'] == 'property'):
		details['name'] = item.get_name()
		details['value'] = str(item.get_value())
		details['type'] = 'string'
		details['origin'] = str(item.get_origin())
	elif(details['kind'] == 'verb'):
		details['names'] = item.get_names()
		details['code'] = str(item.get_code())
		details['origin'] = str(item.get_origin())
	
	p.exchange.queue.send(p.caller.get_id(), dict(
		command			= 'edit',
		details			= details,
	))

@api
def access(p, item):
	result = p.exchange.get_access(item.get_id(), item.get_type())
	
	details = dict(
		id		= item.get_id(),
		type	= item.get_type(),
		access	= [dict(
			rule		= row['rule'],
			access		= row['type'],
			accessor	= str(p.exchange.get_object(row['accessor_id'])) if row['accessor_id'] else row['group'],
			permission	= row['permission_name'],
		) for row in result]
	)
	
	p.exchange.queue.send(p.caller.get_id(), dict(
		command			= 'access',
		details			= details,
	))

@api
def get_object(p, key):
	return p.exchange.get_object(key)

def get_environment(p):
	env = dict(
		command			= p.command,
		caller			= p.caller,
		dobj			= p.dobj,
		dobj_str		= p.dobj_str,
		dobj_spec_str	= p.dobj_spec_str,
		words			= p.words,
		prepositions	= p.prepositions,
		this			= p.this,
		
		system			= p.exchange.get_object(1),
		here			= p.caller.get_location() if p.caller else None,
		
		get_dobj		= p.get_dobj,
		get_dobj_str	= p.get_dobj_str,
		has_dobj		= p.has_dobj,
		has_dobj_str	= p.has_dobj_str,
		
		get_pobj		= p.get_pobj,
		get_pobj_str 	= p.get_pobj_str,
		has_pobj 		= p.has_pobj,
		has_pobj_str 	= p.has_pobj_str,
	)
	
	for name, func in api.locals.items():
		env[name] = func(p)
	
	for name in dir(errors):
		if not(name.endswith('Error')):
			continue
		cls = getattr(errors, name)
		env[name] = cls
	
	return env

