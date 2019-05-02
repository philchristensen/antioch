# antioch
# Copyright (c) 1999-2019 Phil Christensen
#
# See LICENSE for details

import sys, os, os.path, time

from django.test import TestCase
from django.db import connection

from antioch import test
from antioch.core import errors, exchange

# sys.setrecursionlimit(100)

class PermissionsTestCase(TestCase):
    fixtures = ['core-minimal.json']
    
    def setUp(self):
        self.exchange = exchange.ObjectExchange(connection)
        
        self.wizard = self.exchange.get_object('wizard')
        self.user = self.exchange.get_object('user')
    
    def test_defaults(self):
        thing = self.exchange.instantiate('object', name='thing')
        thing.set_owner(self.wizard)
        
        self.assertTrue(self.user.is_allowed('read', thing))
        self.assertFalse(self.user.is_allowed('write', thing))
        self.assertFalse(self.user.is_allowed('entrust', thing))
        self.assertFalse(self.user.is_allowed('move', thing))
        self.assertFalse(self.user.is_allowed('transmute', thing))
        self.assertFalse(self.user.is_allowed('derive', thing))
        self.assertFalse(self.user.is_allowed('develop', thing))
    
    def test_owner_defaults(self):
        thing = self.exchange.instantiate('object', name='thing')
        thing.set_owner(self.user)
        self.assertTrue(self.user.is_allowed('read', thing))
        self.assertTrue(self.user.is_allowed('write', thing))
        self.assertTrue(self.user.is_allowed('entrust', thing))
        self.assertTrue(self.user.is_allowed('move', thing))
        self.assertTrue(self.user.is_allowed('transmute', thing))
        self.assertTrue(self.user.is_allowed('derive', thing))
        self.assertTrue(self.user.is_allowed('develop', thing))
    
    def test_everyone_defaults(self):
        thing = self.exchange.instantiate('object', name='thing')
        jim = self.exchange.instantiate('object', name='Jim', unique_name=True)
        jim.set_player(True, passwd='jim')
        
        self.assertTrue(jim.is_allowed('read', thing))
        self.assertFalse(jim.is_allowed('write', thing))
        self.assertFalse(jim.is_allowed('entrust', thing))
        self.assertFalse(jim.is_allowed('move', thing))
        self.assertFalse(jim.is_allowed('transmute', thing))
        self.assertFalse(jim.is_allowed('derive', thing))
        self.assertFalse(jim.is_allowed('develop', thing))
    
    def test_wizard_defaults(self):
        thing = self.exchange.instantiate('object', name='thing')
        self.assertTrue(self.wizard.is_allowed('read', thing))
        self.assertTrue(self.wizard.is_allowed('write', thing))
        self.assertTrue(self.wizard.is_allowed('entrust', thing))
        self.assertTrue(self.wizard.is_allowed('move', thing))
        self.assertTrue(self.wizard.is_allowed('transmute', thing))
        self.assertTrue(self.wizard.is_allowed('derive', thing))
        self.assertTrue(self.wizard.is_allowed('develop', thing))
    
    def test_simple_deny(self):
        thing = self.exchange.instantiate('object', name='thing')
        thing.set_owner(self.wizard)
        thing.allow('everyone', 'anything')
        thing.deny(self.user, 'write')
        
        self.assertTrue(self.user.is_allowed('read', thing))
        self.assertFalse(self.user.is_allowed('write', thing))
