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
		self.pool = test.init_database(PermissionsTestCase, 'minimal')
		self.exchange = exchange.ObjectExchange(self.pool)
		
		self.wizard = self.exchange.get_object("Wizard")
		self.phil = self.exchange.get_object("Phil")
		self.box = self.exchange.get_object("box")
		self.room = self.exchange.get_object("The Laboratory")
	
	def tearDown(self):
		self.exchange.commit()
		
		self.wizard = None
		self.phil = None
		self.box = None
		self.room = None
	
	def test_defaults(self):
		thing = self.exchange.instantiate('object', name='thing')
		thing.set_owner(self.wizard)
		
		self.failUnless(self.phil.is_allowed('read', thing))
		self.failIf(self.phil.is_allowed('write', thing))
		self.failIf(self.phil.is_allowed('entrust', thing))
		self.failIf(self.phil.is_allowed('move', thing))
		self.failIf(self.phil.is_allowed('transmute', thing))
		self.failIf(self.phil.is_allowed('derive', thing))
		self.failIf(self.phil.is_allowed('develop', thing))
	
	def test_owner_defaults(self):
		self.failUnless(self.phil.is_allowed('read', self.box))
		self.failUnless(self.phil.is_allowed('write', self.box))
		self.failUnless(self.phil.is_allowed('entrust', self.box))
		self.failUnless(self.phil.is_allowed('move', self.box))
		self.failUnless(self.phil.is_allowed('transmute', self.box))
		self.failUnless(self.phil.is_allowed('derive', self.box))
		self.failUnless(self.phil.is_allowed('develop', self.box))
	
	def test_everyone_defaults(self):
		jim = self.exchange.instantiate('object', name='Jim', unique_name=True)
		jim.set_player(True, passwd='jim')
		
		self.failUnless(jim.is_allowed('read', self.box))
		self.failIf(jim.is_allowed('write', self.box))
		self.failIf(jim.is_allowed('entrust', self.box))
		self.failIf(jim.is_allowed('move', self.box))
		self.failIf(jim.is_allowed('transmute', self.box))
		self.failIf(jim.is_allowed('derive', self.box))
		self.failIf(jim.is_allowed('develop', self.box))
	
	def test_wizard_defaults(self):
		self.failUnless(self.wizard.is_allowed('read', self.box))
		self.failUnless(self.wizard.is_allowed('write', self.box))
		self.failUnless(self.wizard.is_allowed('entrust', self.box))
		self.failUnless(self.wizard.is_allowed('move', self.box))
		self.failUnless(self.wizard.is_allowed('transmute', self.box))
		self.failUnless(self.wizard.is_allowed('derive', self.box))
		self.failUnless(self.wizard.is_allowed('develop', self.box))
	
	def test_simple_deny(self):
		thing = self.exchange.instantiate('object', name='thing')
		thing.set_owner(self.wizard)
		thing.allow('everyone', 'anything')
		thing.deny(self.phil, 'write')
		
		self.failUnless(self.phil.is_allowed('read', thing))
		self.failIf(self.phil.is_allowed('write', thing))
