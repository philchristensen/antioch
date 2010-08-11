# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import unittest, string, time, os, os.path, difflib

from txspace import registry, entity, errors, external, minimal, prop, auth, assets, parser, code
from txspace.security import Q

class FalseConnection:
	def get_type(self):
		return 'mock connection'
	def set_observations(self, observations):
		raise errors.UserError(observations)

class ImportExportTestCase(unittest.TestCase):
	def setUp(self):
		self.registry = registry.Registry()
		minimal.init(self.registry, assets.get_verbdir())
		self.test_object = self.registry.new("Test Object")
		
		self.test_object.add_property(Q, 'test', "{u'north': None}", owner=self.registry.get('class_wizard'), eval_type=prop.EVAL_PYTHON)
		self.registry.put(self.test_object)

	def tearDown(self):
		self.registry = None
	
	def test_cycle(self):
		exported_data = external.export(self.registry)
		test_registry = registry.Registry(True)
		external.ingest(test_registry, exported_data);
		
		imported_data = external.export(test_registry)
		try:
			assert exported_data == imported_data, "Exported data changed through import/export cycle."
		except AssertionError, e:
			for line in difflib.unified_diff(exported_data.split("\n"), imported_data.split("\n")):
				print line
			raise e
		
		wizard = test_registry.get('wizard')
		wizard._connection = FalseConnection()
		p = parser.Parser(parser.Lexer("look"), wizard, test_registry)
		verb = p.get_verb()
		env = code.get_environment(wizard, verb, p)
		self.failUnlessRaises(errors.UserError, verb.execute, wizard, env)
	
