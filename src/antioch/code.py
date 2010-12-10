# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Verb execution environment
"""

import time, sys

from antioch import errors, modules, json

allowed_modules = (
	'hashlib',
	'string',
)

def massage_verb_code(code):
	"""
	Take a given piece of verb code and wrap it in a function.
	
	This allows support of 'return' within verbs, and for verbs to return values.
	"""
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
	"""
	Evaluate an expression in the provided environment.
	"""
	if not(environment):
		raise RuntimeError('No environment')
	environment['__name__'] = name
	sys.meta_path = [MetaImporter()]
	value =  eval(code, environment)
	sys.meta_path = []
	return value

def r_exec(code, environment, name="__exec__"):
	"""
	Execute an expression in the provided environment.
	"""
	if not(environment):
		raise RuntimeError('No environment')
	
	code = massage_verb_code(code)
	
	# t = time.time()
	environment['__name__'] = name
	
	sys.meta_path = [MetaImporter()]
	exec(code, environment)
	sys.meta_path = []
	
	# print 'execute took %s seconds' % (time.time() - t)
	
	if("__result__" in environment):
		return environment["__result__"]

def api(func):
	"""
	Mark a function in this module as being part of the verb API.
	"""
	def _api(p):
		def __api(*args, **kwargs):
			return func(p, *args, **kwargs)
		return __api
	
	api.locals = getattr(api, 'locals', {})
	api.locals[func.func_name] = _api
	
	return _api

@api
def task(p, delay, origin, verb_name, *args, **kwargs):
	"""
	Verb API: queue up a new task.
	"""
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
	"""
	Verb API: Return a list of tasks for this user, or all tasks.
	"""
	if(p.caller.is_wizard()):
		return p.exchange.get_tasks()
	else:
		return p.exchange.get_tasks(user_id=p.caller.get_id())

@api
def write(p, user, text, is_error=False, escape_html=True):
	"""
	Verb API: Print a string of text to the user's console.
	"""
	p.exchange.queue.send(user.get_id(), dict(
		command		= 'write',
		text		= str(text),
		is_error	= is_error,
		escape_html	= escape_html,
	))

@api
def observe(p, user, observations):
	"""
	Verb API: Send a dict of observations to the user's client.
	"""
	p.exchange.queue.send(user.get_id(), dict(
		command			= 'observe',
		observations	= observations,
	))

@api
def get_object(p, key):
	"""
	Verb API: Load an object by its global name or ID.
	"""
	return p.exchange.get_object(key)

@api
def create_object(p, name, unique_name=False):
	"""
	Verb API: Create a new object.
	"""
	return p.exchange.instantiate('object', name=name, unique_name=unique_name, owner_id=p.caller.get_id())

def get_environment(p):
	"""
	Given the provided parser object, construct an environment dictionary.
	"""
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

class MetaImporter(object):
	def find_module(self, fullname, path=None):
		print fullname
		if(fullname in allowed_modules):
			return None
		raise ImportError('Restricted: %s' % fullname)
