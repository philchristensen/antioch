# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest
from twisted.internet import defer, error

from antioch import restful, transact

import antioch.modules.registration.transactions as reg_trans
import antioch.modules.editors.transactions as editor_trans

class RestfulTestCase(unittest.TestCase):
	def test_translate_path(self):
		self.failUnlessEqual(restful.translate_path('parse'), 'Parse')
		self.failUnlessEqual(restful.translate_path('update-schema'), 'UpdateSchema')
		self.failUnlessEqual(restful.translate_path('modify-object'), 'ModifyObject')
	
	def test_get_command_class(self):
		self.failUnlessEqual(restful.get_command_class('Parse'), transact.Parse)
		self.failUnlessEqual(restful.get_command_class('UpdateSchema'), reg_trans.UpdateSchema)
		self.failUnlessEqual(restful.get_command_class('ModifyObject'), editor_trans.ModifyObject)

