# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest

from txspace import parser, errors, exchange, test

class ParserTestCase(unittest.TestCase):
	def setUp(self):
		self.pool = test.init_database(ParserTestCase)
		self.exchange = exchange.ObjectExchange(self.pool)
	
	def tearDown(self):
		return self.exchange.dequeue()
	
	def test_parse_verb(self):
		wizard = self.exchange.get_object('wizard')
		p = parser.TransactionParser(parser.Lexer("@eval"), wizard, self.exchange)
		assert not p.has_dobj(), "unexpected object found for dobj"
		assert not p.has_dobj_str(), "unexpected string found for dobj"
		assert not p.prepositions, "unexpected prepositional objects found"
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "on")
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj_str)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj_str, "on")
	
	def test_parse_verb_dobj(self):
		wizard = self.exchange.get_object('wizard')
		p = parser.TransactionParser(parser.Lexer("@eval wizard"), wizard, self.exchange)
		assert p.has_dobj(), "dobj 'wizard' not found"
		assert p.has_dobj_str(), "dobj string 'wizard' not found"
		assert not p.prepositions, "unexpected prepositional objects/strings found"
		self.assertEqual(p.get_dobj(), wizard)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "on")
		self.assertEqual(p.get_dobj_str().lower(), wizard.get_name().lower())
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj_str, "on")
		
	def test_parse_verb_pobj(self):
		wizard = self.exchange.get_object('wizard')
		p = parser.TransactionParser(parser.Lexer("@eval through peephole"), wizard, self.exchange)
		assert not p.has_dobj(), "unexpected object found for dobj"
		assert not p.has_dobj_str(), "unexpected string found for dobj"
		assert p.has_pobj_str('through'), "no prepositional object string found for 'through'"
		assert not p.has_pobj('through'), "no prepositional object found for 'through'"
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchObjectError, p.get_pobj, "through")
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj_str)
		self.assertEqual(p.get_pobj_str("through"), "peephole")
		
	def test_parse_verb_pobj_pobj(self):
		wizard = self.exchange.get_object('wizard')
		p = parser.TransactionParser(parser.Lexer("@eval through peephole with wizard"), wizard, self.exchange)
		assert not p.has_dobj(), "unexpected object found for dobj"
		assert not p.has_dobj_str(), "unexpected string found for dobj"
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "from")
		self.assertEqual(p.get_pobj("with"), wizard)
		self.assertEqual(p.get_pobj_str("with"), "wizard")
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj_str)
		self.assertEqual(p.get_pobj_str("through"), "peephole")
	
	def test_parse_verb_dobj_pobj(self):
		wizard = self.exchange.get_object('wizard')
		p = parser.TransactionParser(parser.Lexer("@eval glasses from wizard with tongs"), wizard, self.exchange)
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "under")
		self.assertEqual(p.get_dobj_str(), "glasses")
		self.assertEqual(p.get_pobj_str("with"), "tongs")
		self.assertEqual(p.get_pobj("from"), wizard)
		self.assertEqual(p.get_pobj_str("from"), "wizard")
	
	def test_complex(self):
		wizard = self.exchange.get_object('wizard')
		p = parser.TransactionParser(parser.Lexer("@eval the wizard from 'bag under stairs' with tongs in wizard's bag"), wizard, self.exchange)
		self.assertRaises(errors.NoSuchObjectError, p.get_pobj, "from")
		self.assertRaises(errors.NoSuchObjectError, p.get_pobj, "with")
		self.assertEqual(p.get_pobj_str('from'), 'bag under stairs')
		self.assertEqual(p.get_dobj(), wizard)
		self.assertEqual(p.get_pobj_str("with"), "tongs")
	
	def test_quoted_strings(self):
		wizard = self.exchange.get_object('wizard')
		p = parser.TransactionParser(parser.Lexer("@eval wizard to 'something here'"), wizard, self.exchange)
		self.assertEqual(p.get_pobj_str('to'), 'something here')
	
	def test_bug_9(self):
		wizard = self.exchange.get_object('wizard')
		p = parser.TransactionParser(parser.Lexer("@eval here as 'Large amounts of chalkdust lay all over the objects in this room, and a large chalkboard at one end has become coated with a thick layer of Queen Anne\\'s lace. Strange semi-phosphorescant orbs are piled all around this ancient hall.'"), wizard, self.exchange)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj_str, 'around')
		assert "\\" not in p.get_pobj_str('as')
	
	def test_inventory(self):
		wizard = self.exchange.get_object('wizard')
		box = self.exchange.instantiate('object', name='box')
		box.set_location(wizard)
		
		p = parser.TransactionParser(parser.Lexer("@eval my box"), wizard, self.exchange)
		self.failUnless(p.has_dobj())
		
		user = self.exchange.get_object('user')
		box.set_location(user)
		
		p = parser.TransactionParser(parser.Lexer("@eval user's box"), wizard, self.exchange)
		self.failUnless(p.has_dobj())

