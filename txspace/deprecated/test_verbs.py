# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

import unittest, string, sys, os, os.path

from txspace import registry, parser, errors, minimal, auth, verb, code, assets

class FalseConnection:
	def get_type(self):
		return 'mock connection'
	def set_observations(self, observations):
		raise errors.UserError(observations)

class VerbTestCase(unittest.TestCase):
	def setUp(self):
		self.registry = registry.Registry()
		minimal.init(self.registry, assets.get_verbdir())
	
	def tearDown(self):
		self.registry = None
		
	def test_ancestry(self):
		wizard = self.registry.get('wizard')
		class_player = self.registry.get('class_player')
		ancestor = wizard.get_ancestor_with(wizard, 'look')
		assert ancestor is class_player, "Didn't get class_player as ancestor of wizard"
		assert isinstance(ancestor._vdict['look'], verb.Verb), "Result wasn't a verb"
	
	def test_look(self):
		wizard = self.registry.get('wizard')
		wizard._connection = FalseConnection()
		p = parser.Parser(parser.Lexer("look"), wizard, self.registry)
		verb = p.get_verb()
		env = code.get_environment(wizard, verb, p)
		self.failUnlessRaises(errors.UserError, verb.execute, wizard, env)
