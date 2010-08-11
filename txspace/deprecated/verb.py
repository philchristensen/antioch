# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Verb


"""

import copy

from txspace import code, parser, auth, security
from txspace.security import Q

class Verb:
	def __init__(self, ctx, code, names, **kwargs):
		if(ctx is Q and 'owner' not in kwargs):
			raise KeyError("When creating a Verb in the Q context, an 'owner' keyword argument is required.")
		
		self._vitals = dict(
			acl			= [],
			names		= names,
			owner		= kwargs.get('owner', ctx),
			code		= code, 
			origin		= kwargs['origin'],
			is_ability	= kwargs.get('is_ability', False),
			is_method	= kwargs.get('is_method', False),
		)
		
		acl_config = kwargs.get('acl_config', security.default_verb_acl)
		acl_config(self)
	
	def __getstate__(self):
		"""
		When this gets saved to disk, we get rid of
		the client reference.
		"""
		state = self.__dict__.copy()
		if(state['_vitals'].has_key('cache')):
			del state['_vitals']['cache']
		return state
	
	def __setstate__(self, state):
		"""
		See __getstate__
		"""
		for key in state.keys():
			self.__dict__[key] = state[key]
	
	def execute(self, ctx, env):
		security.check_allowed(ctx, "execute", self)
		# We're going to modify the code here so that it's within a
		# function definition. That way, verb code can use "return"
		# to abort execution.
		if('cache' not in self._vitals):
			lines = self._vitals['code'].split("\n")
			final_code = "def ___verb_code___():\n"
			for line in lines:
				final_code += ("\t" + line + "\n")
			final_code += "\n__result__ = ___verb_code___()\n"
			self._vitals['cache'] = compile(final_code, str(self._vitals['origin']) + ":" + self._vitals['names'][0], 'exec')
		return code.r_exec(ctx, self._vitals['cache'], env)

	def call(self, ctx, source, args, kwargs):
		security.check_allowed(ctx, "execute", self)
		registry = self._vitals['origin'].get_registry(Q)
		p = parser.Parser(parser.Lexer(""), ctx, registry)
		
		from txspace import entity
		env = dict(
			args = args,
			kwargs = kwargs,
			this = source,
		)
		env = code.get_environment(ctx, self, p, env)
		
		return self.execute(ctx, env)
		
	def get_owner(self, ctx):
		security.check_allowed(ctx, "read", self)
		return self._vitals['owner']
	
	def get_names(self, ctx):
		security.check_allowed(ctx, "read", self)
		return copy.copy(self._vitals['names'])
	
	def set_names(self, ctx, names):
		security.check_allowed(ctx, "write", self)
		self._vitals['names'] = names
	
	def is_ability(self, ctx):
		security.check_allowed(ctx, "read", self)
		return self._vitals['is_ability']
	
	def is_method(self, ctx):
		security.check_allowed(ctx, "read", self)
		return self._vitals['is_method']
	
	def is_readable(self, ctx):
		return security.is_allowed(ctx, "read", self);
	
	def is_writeable(self, ctx):
		return security.is_allowed(ctx, "write", self);
	
	def is_executeable(self, ctx):
		return security.is_allowed(ctx, "execute", self);
	
	def get_code(self, ctx):
		security.check_allowed(ctx, "read", self);
		return self._vitals['code']