# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest
from twisted.internet import defer
from twisted.cred import credentials

from txspace import exchange, test, auth, transact, errors

class AuthenticationTestCase(unittest.TestCase):
	def setUp(self):
		self.pool = test.init_database(AuthenticationTestCase)
		self.exchange = exchange.ObjectExchange(self.pool)
	
	@defer.inlineCallbacks
	def tearDown(self):
		yield transact.shutdown()	

	@defer.inlineCallbacks
	def test_checker_failed(self):
		checker = auth.TransactionChecker()
		creds = credentials.UsernamePassword('asdfgasd', 'adsfgsdfg')
		
		failed = False
		try:
			avatar_id = yield checker.requestAvatarId(creds)
		except errors.PermissionError, e:
			failed = True
		
		self.failUnless(failed, "Didn't raise errors.PermissionError")
	
	@defer.inlineCallbacks
	def test_checker_passed(self):
		checker = auth.TransactionChecker()
		creds = credentials.UsernamePassword('Wizard', 'wizard')
		avatar_id = yield checker.requestAvatarId(creds)
		self.failUnlessEqual(avatar_id, 2)
