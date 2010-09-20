# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest
from twisted.internet import defer

from txspace import test, errors, exchange, dbapi, parser, transact

class TransactionTestCase(unittest.TestCase):
	def setUp(self):
		self.pool = test.init_database(TransactionTestCase)
		self.exchange = exchange.ObjectExchange(self.pool)
	
	@defer.inlineCallbacks
	def tearDown(self):
		yield transact.shutdown()	
	
	def test_basic_rollback(self):
		try:
			with self.exchange as x:
				x.instantiate('object', name="Test Object")
				raise RuntimeError()
		except:
			pass
		
		self.failUnlessRaises(errors.NoSuchObjectError, x.get_object, "Test Object")
	
	def test_parser_rollback(self):
		created = False
		user_id = 2 # Wizard ID
		try:
			with self.exchange as x:
				caller = x.get_object(user_id)
				parser.parse(caller, '@exec create_object("Test Object")')
				if(x.get_object('Test Object')):
					created = True
				parser.parse(caller, '@exec raise RuntimeError()')
		except:
			pass
		
		self.failUnless(created, "'Test Object' not created.")
		self.failUnlessRaises(errors.NoSuchObjectError, x.get_object, "Test Object")
