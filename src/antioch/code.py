# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Provide the verb execution environment
"""

import time, sys, os.path

from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins

from antioch import errors, modules, json

allowed_modules = (
	'hashlib',
	'string',
)

def is_frame_access_allowed():
	"""
	Used by get/setattr to delegate access.
	
	Returns True if the call to __getattribute__ or __setattr__ originated
	in either the exchange, test, or bootstrap modules.
	
	Previously this used inspect, which made it super slow. The only potential
	issue with using _getframe() is that it's not guaranteed to be there in
	non CPython implementations.
	"""
	f = sys._getframe(1)
	c1 = f.f_back.f_code
	c2 = f.f_back.f_back.f_code
	try:
		from antioch import model
		model_source_path = os.path.abspath(model.__file__)
		if(model_source_path.endswith('pyc')):
			model_source_path = model_source_path[:-1]
		if(c2.co_filename == model_source_path):
			#print '%r =(1)= %r' % (c2.co_filename, model_source_path)
			return True
		
		from antioch import exchange
		exchange_source_path = os.path.abspath(exchange.__file__)
		if(exchange_source_path.endswith('pyc')):
			exchange_source_path = exchange_source_path[:-1]
		if(c2.co_filename == exchange_source_path):
			#print '%r =(2)= %r' % (c2.co_filename, exchange_source_path)
			return True
		
		from antioch import test
		test_source_path = os.path.abspath(os.path.dirname(test.__file__))
		if(c2.co_filename.startswith(test_source_path)):
			#print '%r 1startswith %r' % (c2.co_filename, test_source_path)
			return True
		
		from antioch import assets
		bootstrap_source_path = os.path.abspath(os.path.join(os.path.dirname(assets.__file__), 'bootstraps'))
		if(c2.co_filename.startswith(bootstrap_source_path)):
			#print '%r 2startswith %r' % (c2.co_filename, bootstrap_source_path)
			return True
		
		return False
	finally:
		del c2
		del c1
		del f

def massage_verb_code(code):
	"""
	Take a given piece of verb code and wrap it in a function.
	
	This allows support of 'return' within verbs, and for verbs to return values.
	"""
	code = code.replace('\r\n', '\n')
	code = code.replace('\n\r', '\n')
	code = code.replace('\r', '\n')
	code = '\n'.join(
		['def verb():'] +
		['\t' + x for x in code.split('\n') if x.strip()] +
		['returnValue = verb()']
	)
	return code

def r_eval(caller, src, environment={}, filename='<string>', runtype="eval"):
	"""
	Evaluate an expression in the provided environment.
	"""
	def _writer(s):
		if(s.strip()):
			write(environment.get('parser'))(caller, s)
	
	env = get_restricted_environment(_writer, environment.get('parser'))
	env['runtype'] = runtype
	env['caller'] = caller
	env.update(environment)
	
	code = compile_restricted(src, filename, 'eval')
	value =  eval(code, env)
	return value

def r_exec(caller, src, environment={}, filename='<string>', runtype="exec"):
	"""
	Execute an expression in the provided environment.
	"""
	def _writer(s):
		if(s.strip()):
			write(environment.get('parser'))(caller, s)
	
	# t = time.time()
	env = get_restricted_environment(_writer, environment.get('parser'))
	env['runtype'] = runtype
	env['caller'] = caller
	env.update(environment)
	
	code = compile_restricted(massage_verb_code(src), filename, 'exec')
	exec code in env
	# print 'execute took %s seconds' % (time.time() - t)
	if("returnValue" in env):
		return env["returnValue"]

def restricted_import(name, gdict, ldict, fromlist, level=-1):
	"""
	Used to drastically limit the importable modules.
	"""
	if(name in allowed_modules):
		return __builtins__['__import__'](name, gdict, ldict, fromlist, level)
	raise ImportError('Restricted: %s' % name)

def get_protected_attribute(obj, name, g=getattr):
	if(name.startswith('_') and not is_frame_access_allowed()):
		raise AttributeError(name)
	return g(obj, name)

def set_protected_attribute(obj, name, value, s=setattr):
	if(name.startswith('_') and not is_frame_access_allowed()):
		raise AttributeError(name)
	return s(obj, name, value)

def get_restricted_environment(writer, p=None):
	"""
	Given the provided parser object, construct an environment dictionary.
	"""
	class _print_(object):
		def write(self, s):
			writer(s)
	
	class _write_(object):
		def __init__(self, obj):
			object.__setattr__(self, 'obj', obj)
		
		def __setattr__(self, name, value):
			"""
			Private attribute protection using is_frame_access_allowed()
			"""
			set_protected_attribute(self.obj, name, value)
	
	safe_builtins['__import__'] = restricted_import
	
	for name in ['dict', 'getattr', 'hasattr']:
		safe_builtins[name] = __builtins__[name]
	
	env = dict(
		_print_			= lambda: _print_(),
		_write_			= _write_,
		_getattr_		= get_protected_attribute,
		_getitem_		= lambda obj, key: obj[key],
		_getiter_		= lambda obj: iter(obj),
		__import__		= restricted_import,
		__builtins__	= safe_builtins,
	)
	
	for mod in modules.iterate():
		for name, func in mod.get_environment().items():
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
def execute(p, code):
	"""
	Verb API: Execute the code in place.
	"""
	return r_exec(p.caller, code, p.get_environment())


@api
def evaluate(p, code):
	"""
	Verb API: Evalue the expression in place.
	"""
	return r_eval(p.caller, code, p.get_environment())

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

