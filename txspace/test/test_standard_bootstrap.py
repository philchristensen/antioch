# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest

from txspace import parser, exchange, test

class StandardBootstrapTestCase(unittest.TestCase):
	def setUp(self):
		self.pool = test.init_database(StandardBootstrapTestCase, 'standard')
		self.exchange = exchange.ObjectExchange(self.pool)
		self.exchange.queue = test.Anything(
			commit	= lambda: None,
		)
	
	def tearDown(self):
		return self.exchange.commit()
	
	def test_player_look(self):
		caller = self.exchange.get_object('phil')
		
		l = parser.Lexer('look here')
		p = parser.TransactionParser(l, caller, self.exchange)
		
		v = p.get_verb()
		self.failUnlessEqual(p.this, caller)
		
		def send(user_id, msg):
			self.failUnlessEqual(user_id, 9L)
			self.failUnlessEqual(msg['observations']['name'], 'The Laboratory')
		
		self.exchange.queue.send = send
		v.execute(p)
	
	def test_player_multiparent_look(self):
		caller = self.exchange.get_object('phil')
		random = self.exchange.new('random')
		caller.add_parent(random)
		
		l = parser.Lexer('look here')
		p = parser.TransactionParser(l, caller, self.exchange)
		
		v = p.get_verb()
		self.failUnlessEqual(p.this, caller)
		
		def send(user_id, msg):
			self.failUnlessEqual(user_id, 9L)
			self.failUnlessEqual(msg['observations']['name'], 'The Laboratory')
		
		self.exchange.queue.send = send
		v.execute(p)
	
	def test_wizard_edit(self):
		caller = self.exchange.get_object('wizard')
		
		l = parser.Lexer('@edit me')
		p = parser.TransactionParser(l, caller, self.exchange)
		
		v = p.get_verb()
		self.failUnlessEqual(p.this, caller)
		
		def send(user_id, msg):
			self.failUnlessEqual(user_id, 2L)
			self.failUnlessEqual(msg['details']['name'], 'Wizard')
		
		self.exchange.queue.send = send
		v.execute(p)
