# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest

from antioch import test
from antioch.core import parser, exchange

class DefaultBootstrapTestCase(unittest.TestCase):
	def setUp(self):
		self.pool = test.init_database(self.__class__, dataset='default')
		self.exchange = exchange.ObjectExchange(self.pool)
		self.exchange.queue = test.Anything(
			flush	= lambda: None,
		)
	
	def tearDown(self):
		return self.exchange.flush()
	
	def test_player_look(self):
		caller = self.exchange.get_object('wizard')
		
		l = parser.Lexer('look here')
		p = parser.TransactionParser(l, caller, self.exchange)
		
		v = p.get_verb()
		self.failUnlessEqual(p.this, caller)
		
		def push(user_id, msg):
			self.failUnlessEqual(user_id, caller.get_id())
			self.failUnlessEqual(msg['observations']['name'], 'The Laboratory')
		
		self.exchange.queue.push = push
		v.execute(p)
	
	def test_player_eval(self):
		caller = self.exchange.get_object('wizard')
		
		l = parser.Lexer('@eval "test"')
		p = parser.TransactionParser(l, caller, self.exchange)
		
		v = p.get_verb()
		self.failUnlessEqual(p.this, caller)
		
		self._test_player_eval_ran = False
		
		def push(user_id, msg):
			self._test_player_eval_ran = True
			self.failUnlessEqual(user_id, 2L)
			self.failUnlessEqual(msg['text'], 'test')
		
		self.exchange.queue.push = push
		v.execute(p)
		
		self.failUnlessEqual(self._test_player_eval_ran, True)
	
	def test_player_write(self):
		caller = self.exchange.get_object('wizard')
		
		l = parser.Lexer('@exec write(caller, "test")')
		p = parser.TransactionParser(l, caller, self.exchange)
		
		v = p.get_verb()
		self.failUnlessEqual(p.this, caller)
		
		self._test_player_write_ran = False
		
		def push(user_id, msg):
			self._test_player_write_ran = True
			self.failUnlessEqual(user_id, 2L)
			self.failUnlessEqual(msg['text'], 'test')
		
		self.exchange.queue.push = push
		v.execute(p)
		
		self.failUnlessEqual(self._test_player_write_ran, True)
	
	def test_player_multiparent_look(self):
		caller = self.exchange.get_object('wizard')
		random = self.exchange.instantiate('object', name='random')
		caller.add_parent(random)
		
		l = parser.Lexer('look here')
		p = parser.TransactionParser(l, caller, self.exchange)
		
		v = p.get_verb()
		self.failUnlessEqual(p.this, caller)
		
		def push(user_id, msg):
			self.failUnlessEqual(user_id, caller.get_id())
			self.failUnlessEqual(msg['observations']['name'], 'The Laboratory')
		
		self.exchange.queue.push = push
		v.execute(p)
	
	def test_wizard_edit(self):
		caller = self.exchange.get_object('wizard')
		
		l = parser.Lexer('@edit me')
		p = parser.TransactionParser(l, caller, self.exchange)
		
		v = p.get_verb()
		self.failUnlessEqual(p.this, caller)
		
		def push(user_id, msg):
			self.failUnlessEqual(user_id, 2L)
			self.failUnlessEqual(msg['details']['name'], 'Wizard')
		
		self.exchange.queue.push = push
		v.execute(p)
	
	def test_wizard_edit_system(self):
		caller = self.exchange.get_object('wizard')
		
		l = parser.Lexer('@edit #1')
		p = parser.TransactionParser(l, caller, self.exchange)
		
		v = p.get_verb()
		self.failUnlessEqual(p.this, caller)
		
		def push(user_id, msg):
			self.failUnlessEqual(user_id, 2L)
			self.failUnlessEqual(msg['details']['id'], 1)
			self.failUnlessEqual(msg['details']['name'], 'System Object')
		
		self.exchange.queue.push = push
		v.execute(p)
