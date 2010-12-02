# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Code
"""

import time

from antioch import errors, modules, json

def massage_verb_code(code):
	code = code.replace('\r\n', '\n')
	code = code.replace('\n\r', '\n')
	code = code.replace('\r', '\n')
	code = '\n'.join(
		['def __verb__():'] +
		['\t' + x for x in code.split('\n') if x.strip()] +
		['__result__ = __verb__()']
	)
	return code

def r_eval(code, environment, name="__eval__"):
	if not(environment):
		raise RuntimeError('No environment')
	environment['__name__'] = name
	return eval(code, environment)

def r_exec(code, environment, name="__exec__"):
	if not(environment):
		raise RuntimeError('No environment')
	
	code = massage_verb_code(code)
	
	# t = time.time()
	environment['__name__'] = name
	exec(code, environment)
	# print 'execute took %s seconds' % (time.time() - t)
	
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
def task(p, delay, origin, verb_name, *args, **kwargs):
	#force exception here if undumpable
	p.exchange.queue.send(p.caller, dict(
		command		= 'task',
		delay		= int(delay),
		origin		= str(origin),
		verb_name	= str(verb_name),
		args		= json.dumps(args),
		kwargs		= json.dumps(kwargs),
	))

@api
def tasks(p):
	if(p.caller.is_wizard()):
		return p.exchange.get_tasks()
	else:
		return p.exchange.get_tasks(user_id=p.caller.get_id())

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
def get_object(p, key):
	return p.exchange.get_object(key)

@api
def create_object(p, name, unique_name=False):
	return p.exchange.instantiate('object', name=name, unique_name=unique_name, owner_id=p.caller.get_id())

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
		self			= p.verb,
		
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
	
	for mod in modules.iterate():
		for name, func in mod.get_environment(p).items():
			func.func_name = name
			api(func) if callable(func) else None
	
	for name, func in api.locals.items():
		env[name] = func(p)
	
	for name in dir(errors):
		if not(name.endswith('Error')):
			continue
		cls = getattr(errors, name)
		env[name] = cls
	
	return env

