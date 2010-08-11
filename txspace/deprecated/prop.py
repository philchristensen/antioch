# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Property


"""

try:
	import cPickle as pickle
except:
	import pickle

from txspace import code, auth, parser, security
from txspace.security import Q

EVAL_STRING = 0
EVAL_PYTHON = 1
EVAL_DYNAMIC_CODE = 2

class Property:	
	def __init__(self, ctx, value, **kwargs):
		"""
		Create a new property object.
		"""
		if(ctx is Q and 'owner' not in kwargs):
			raise KeyError("When creating a Property in the Q context, an 'owner' keyword argument is required.")
		
		self._vitals = dict(
			acl			= [],
			owner		= kwargs.get('owner', ctx),
			origin		= kwargs['origin'],
			needs_eval	= False,
			eval_type	= int(kwargs.get('eval_type', EVAL_STRING)),
			value		= None,
			code		= None,
		)
		
		acl_config = kwargs.get('acl_config', security.default_property_acl)
		acl_config(self)
		
		self.set_value(ctx, value)
		
	def set_value(self, ctx, value, evaluate=False):
		if(self.get_eval_type(ctx) == EVAL_STRING):
			self._vitals['value'] = value
		elif(self.get_eval_type(ctx) == EVAL_DYNAMIC_CODE):
			self._vitals['code'] = value
		elif(self.get_eval_type(ctx) == EVAL_PYTHON):
			if(evaluate):
				self._vitals['code'] = value
				self._vitals['needs_eval'] = True
			else:
				self._vitals['code'] = repr(value)
				self._vitals['value'] = value
		else:
			raise TypeError("Invalid property type: '%s'" % str(self.get_eval_type(ctx)))
	
	def get_value(self, ctx):
		"""
		Get the value of this property.
		"""
		security.check_allowed(ctx, "read", self)
		registry = self.get_origin(ctx).get_registry(Q)
		
		if(self.get_eval_type(ctx) in (EVAL_DYNAMIC_CODE, EVAL_PYTHON)):
			p = parser.Parser(parser.Lexer(""), ctx, registry)
			env = code.get_environment(ctx, None, p)
			env['this'] = self.get_origin(ctx)
			
			if(self.get_eval_type(ctx) == EVAL_DYNAMIC_CODE):
				self._vitals['value'] = self.evaluate(ctx, env)
			elif(self.get_eval_type(ctx) == EVAL_PYTHON and self._vitals['needs_eval']):
				self._vitals['value'] = code.r_eval(ctx, self.get_code(ctx), env)
				self._vitals['needs_eval'] = False
		
		return self._vitals['value']
	
	def evaluate(self, ctx, ):
		security.check_allowed(ctx, "execute", self)
		lines = self._vitals['code'].split("\n")
		final_code = "def ___prop_code___():\n"
		for line in lines:
			final_code += ("\t" + line + "\n")
		final_code += "\n__result__ = ___prop_code___()\n"
		return code.r_exec(ctx, final_code, env)
	
	def get_code(self, ctx):
		security.check_allowed(ctx, "read", self)
		return self._vitals['code']
	
	def clone(self, ctx, origin):
		result = Property(ctx, self._vitals['value'], origin=origin, eval_type=self.get_eval_type(ctx))
		return result
	
	def get_owner(self, ctx):
		"""
		Get the owner of this property.
		"""
		security.check_allowed(ctx, "read", self)
		return self._vitals['owner']
	
	def get_origin(self, ctx):
		"""
		Get the owner of this property.
		"""
		security.check_allowed(ctx, "read", self)
		return self._vitals['origin']
	
	def get_eval_type(self, ctx):
		security.check_allowed(ctx, "read", self)
		return self._vitals['eval_type']
	
	def set_eval_type(self, ctx, eval_type):
		security.check_allowed(ctx, "write", self)
		self._vitals['eval_type'] = eval_type
	
	def is_readable(self, ctx):
		"""
		Is this property readable by the public?
		"""
		return security.is_allowed(ctx, 'read', self)
	
	def is_writeable(self, ctx):
		"""
		Is this property editable by the public?
		"""
		return security.is_allowed(ctx, 'write', self)
	
	def is_inherited(self, ctx):
		"""
		Does this property change ownership in descendents?
		TODO: make this work right
		"""
		return security.is_allowed(ctx, 'inherit', self)