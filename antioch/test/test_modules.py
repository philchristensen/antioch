# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest

from antioch import modules

class ModulesTestCase(unittest.TestCase):
	def test_find_core_module(self):
		from antioch.modules.core import plugin
		mod = modules.get('core')
		self.assertEqual(mod, plugin)