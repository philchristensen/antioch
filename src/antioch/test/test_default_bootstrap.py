# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest

from antioch import parser, exchange, test

class DefaultBootstrapTestCase(unittest.TestCase):
	def setUp(self):
		self.pool = test.init_database(DefaultBootstrapTestCase, dataset='default')
		self.exchange = exchange.ObjectExchange(self.pool)
		self.exchange.queue = test.Anything(
			commit	= lambda: None,
		)
	
	def tearDown(self):
		return self.exchange.dequeue()
	
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
		random = self.exchange.instantiate('object', name='random')
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
	
	def test_wizard_edit_system(self):
		caller = self.exchange.get_object('wizard')
		
		l = parser.Lexer('@edit #1')
		p = parser.TransactionParser(l, caller, self.exchange)
		
		v = p.get_verb()
		self.failUnlessEqual(p.this, caller)
		
		def send(user_id, msg):
			self.failUnlessEqual(user_id, 2L)
			self.failUnlessEqual(msg['details']['id'], 1)
			self.failUnlessEqual(msg['details']['name'], 'System Object')
		
		self.exchange.queue.send = send
		v.execute(p)
