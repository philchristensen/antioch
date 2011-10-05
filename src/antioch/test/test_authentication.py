# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest
from twisted.internet import defer
from twisted.cred import credentials, error

from antioch import exchange, test, auth, transact, errors, conf

class AuthenticationTestCase(unittest.TestCase):
	def setUp(self):
		self.pool = test.init_database(self.__class__)
		self.test_db_url = conf.get('db-url-test')
	
	@defer.inlineCallbacks
	def tearDown(self):
		yield transact.shutdown()	

	@defer.inlineCallbacks
	def test_checker_failed(self):
		checker = auth.TransactionChecker(db_url=self.test_db_url)
		creds = credentials.UsernamePassword('asdfgasd', 'adsfgsdfg')
		creds.ip_address = '127.0.0.1'
		
		try:
			avatar_id = yield checker.requestAvatarId(creds)
		except error.UnauthorizedLogin, e:
			pass
		else:
			self.fail("Didn't raise error.UnauthorizedLogin")
	
	@defer.inlineCallbacks
	def test_checker_passed(self):
		user_id = None
		with exchange.ObjectExchange(self.pool) as x:
			if(x.refs('test_checker_passed_user')):
				u = x.get_object("test_checker_passed_user")
			else:
				u = x.instantiate('object', name="test_checker_passed_user")
				u.set_player(True, passwd='test_checker_passed_password')
			user_id = u.get_id()
		
		checker = auth.TransactionChecker(db_url=self.test_db_url)
		creds = credentials.UsernamePassword('test_checker_passed_user', 'test_checker_passed_password')
		creds.ip_address = '127.0.0.1'
		avatar_id = yield checker.requestAvatarId(creds)
		self.failUnlessEqual(avatar_id, user_id)
