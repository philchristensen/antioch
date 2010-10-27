# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest
from twisted.internet import defer, error

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
	
	@defer.inlineCallbacks
	def test_timeout(self):
		if(transact.code_timeout is None):
			raise unittest.SkipTest("Code timeout disabled.")
		terminated = False
		user_id = 2 # Wizard ID
		try:
			result = yield transact.Parse.run(user_id=user_id, sentence='@exec import time; time.sleep(20)')
		except error.ProcessTerminated, e:
			terminated = True
		
		self.failUnless(terminated, "Pool did not throw ProcessTerminated")
	
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
	
	def test_protected_attribute_access(self):
		user_id = 2 # Wizard ID
		with self.exchange as x:
			wizard = x.get_object(user_id)
			self.failUnlessEqual(wizard._location_id, wizard.get_location().get_id())
		
		with exchange.ObjectExchange(self.pool, ctx=user_id) as x:
			wizard = x.get_object(user_id)
			eval_verb = x.get_verb(user_id, '@eval')
			
			# since this will raise AttributeError, the model will attempt to find a verb by that name
			self.failUnlessRaises(errors.NoSuchVerbError, getattr, wizard, '_location_id')
			
			self.failUnlessRaises(AttributeError, getattr, eval_verb, '_origin_id')
			self.failUnlessRaises(AttributeError, getattr, eval_verb, '__dict__')
			self.failUnlessRaises(AttributeError, getattr, eval_verb, '__slots__')
		