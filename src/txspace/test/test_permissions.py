# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

import sys, os, os.path, time

from twisted.trial import unittest

from txspace import errors, exchange, test, dbapi

# dbapi.debug = 1
# sys.setrecursionlimit(100)

class PermissionsTestCase(unittest.TestCase):
	def setUp(self):
		self.pool = test.init_database(PermissionsTestCase)
		self.exchange = exchange.ObjectExchange(self.pool)
		
		self.wizard = self.exchange.get_object('wizard')
		self.user = self.exchange.get_object('user')
	
	def test_defaults(self):
		thing = self.exchange.instantiate('object', name='thing')
		thing.set_owner(self.wizard)
		
		self.failUnless(self.user.is_allowed('read', thing))
		self.failIf(self.user.is_allowed('write', thing))
		self.failIf(self.user.is_allowed('entrust', thing))
		self.failIf(self.user.is_allowed('move', thing))
		self.failIf(self.user.is_allowed('transmute', thing))
		self.failIf(self.user.is_allowed('derive', thing))
		self.failIf(self.user.is_allowed('develop', thing))
	
	def test_owner_defaults(self):
		thing = self.exchange.instantiate('object', name='thing')
		thing.set_owner(self.user)
		self.failUnless(self.user.is_allowed('read', thing))
		self.failUnless(self.user.is_allowed('write', thing))
		self.failUnless(self.user.is_allowed('entrust', thing))
		self.failUnless(self.user.is_allowed('move', thing))
		self.failUnless(self.user.is_allowed('transmute', thing))
		self.failUnless(self.user.is_allowed('derive', thing))
		self.failUnless(self.user.is_allowed('develop', thing))
	
	def test_everyone_defaults(self):
		thing = self.exchange.instantiate('object', name='thing')
		jim = self.exchange.instantiate('object', name='Jim', unique_name=True)
		jim.set_player(True, passwd='jim')
		
		self.failUnless(jim.is_allowed('read', thing))
		self.failIf(jim.is_allowed('write', thing))
		self.failIf(jim.is_allowed('entrust', thing))
		self.failIf(jim.is_allowed('move', thing))
		self.failIf(jim.is_allowed('transmute', thing))
		self.failIf(jim.is_allowed('derive', thing))
		self.failIf(jim.is_allowed('develop', thing))
	
	def test_wizard_defaults(self):
		thing = self.exchange.instantiate('object', name='thing')
		self.failUnless(self.wizard.is_allowed('read', thing))
		self.failUnless(self.wizard.is_allowed('write', thing))
		self.failUnless(self.wizard.is_allowed('entrust', thing))
		self.failUnless(self.wizard.is_allowed('move', thing))
		self.failUnless(self.wizard.is_allowed('transmute', thing))
		self.failUnless(self.wizard.is_allowed('derive', thing))
		self.failUnless(self.wizard.is_allowed('develop', thing))
	
	def test_simple_deny(self):
		thing = self.exchange.instantiate('object', name='thing')
		thing.set_owner(self.wizard)
		thing.allow('everyone', 'anything')
		thing.deny(self.user, 'write')
		
		self.failUnless(self.user.is_allowed('read', thing))
		self.failIf(self.user.is_allowed('write', thing))
