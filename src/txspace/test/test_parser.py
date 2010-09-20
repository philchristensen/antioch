# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest

from txspace import parser, errors, exchange, test

class ParserTestCase(unittest.TestCase):
	def setUp(self):
		self.pool = test.init_database(ParserTestCase, 'minimal')
		self.exchange = exchange.ObjectExchange(self.pool)
		self.queue = test.Anything()
		
		self.wizard = self.exchange.get_object("Wizard")
		self.box = self.exchange.get_object("box")
		self.room = self.exchange.get_object("The Laboratory")
	
	def tearDown(self):
		self.wizard = None
		self.box = None
		self.room = None
		
		return self.exchange.commit()
	
	def test_parse_verb(self):
		results = [
			dict(
				command			= 'observe',
				observations	= dict(
					contents	= [
						dict(
							image	= None,
							mood	= None,
							name	= 'Wizard',
							type	= True,
						),
						dict(
							image	= None,
							mood	= None,
							name	= 'Phil',
							type	= True,
						),
						dict(
							image	= None,
							mood	= None,
							name	= 'box',
							type	= False,
						),
					],
					description	= 'Nothing much to see here.',
					id			= 3L,
					location_id	= 0,
					name		= 'The Laboratory',
				)
			)
		]
		
		p = parser.TransactionParser(parser.Lexer("look"), self.wizard, self.exchange)
		assert not p.has_dobj(), "unexpected object found for dobj"
		assert not p.has_dobj_str(), "unexpected string found for dobj"
		assert not p.prepositions, "unexpected prepositional objects found"
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "on")
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj_str)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj_str, "on")
		
		self.exchange.queue = test.Anything(
			send	= lambda u, m: self.failUnlessEqual(results.pop(), m),
			commit	= lambda: None,
		)
		v = p.get_verb()
		v.execute(p)
	
	def test_parse_verb_dobj(self):
		p = parser.TransactionParser(parser.Lexer("look wizard"), self.wizard, self.exchange)
		assert p.has_dobj(), "dobj 'wizard' not found"
		assert p.has_dobj_str(), "dobj string 'wizard' not found"
		assert not p.prepositions, "unexpected prepositional objects/strings found"
		self.assertEqual(p.get_dobj(), self.wizard)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "on")
		self.assertEqual(p.get_dobj_str().lower(), self.wizard.get_name().lower())
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj_str, "on")
		
	def test_parse_verb_pobj(self):
		p = parser.TransactionParser(parser.Lexer("look through peephole"), self.wizard, self.exchange)
		assert not p.has_dobj(), "unexpected object found for dobj"
		assert not p.has_dobj_str(), "unexpected string found for dobj"
		assert p.has_pobj_str('through'), "no prepositional object string found for 'through'"
		assert not p.has_pobj('through'), "no prepositional object found for 'through'"
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchObjectError, p.get_pobj, "through")
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj_str)
		self.assertEqual(p.get_pobj_str("through"), "peephole")
		
	def test_parse_verb_pobj_pobj(self):
		p = parser.TransactionParser(parser.Lexer("look through peephole with box"), self.wizard, self.exchange)
		assert not p.has_dobj(), "unexpected object found for dobj"
		assert not p.has_dobj_str(), "unexpected string found for dobj"
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "from")
		self.assertEqual(p.get_pobj("with"), self.box)
		self.assertEqual(p.get_pobj_str("with"), "box")
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj_str)
		self.assertEqual(p.get_pobj_str("through"), "peephole")
	
	def test_parse_verb_dobj_pobj(self):
		p = parser.TransactionParser(parser.Lexer("take glasses from wizard with tongs"), self.wizard, self.exchange)
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "under")
		self.assertEqual(p.get_dobj_str(), "glasses")
		self.assertEqual(p.get_pobj_str("with"), "tongs")
		self.assertEqual(p.get_pobj("from"), self.wizard)
		self.assertEqual(p.get_pobj_str("from"), "wizard")
	
	def test_complex(self):
		p = parser.TransactionParser(parser.Lexer("take the box from 'bag under stairs' with tongs in wizard's bag"), self.wizard, self.exchange)
		self.assertRaises(errors.NoSuchObjectError, p.get_pobj, "from")
		self.assertRaises(errors.NoSuchObjectError, p.get_pobj, "with")
		self.assertEqual(p.get_pobj_str('from'), 'bag under stairs')
		self.assertEqual(p.get_dobj(), self.box)
		self.assertEqual(p.get_pobj_str("with"), "tongs")
	
	def test_quoted_strings(self):
		p = parser.TransactionParser(parser.Lexer("@passwd wizard to 'something here'"), self.wizard, self.exchange)
		self.assertEqual(p.get_pobj_str('to'), 'something here')
	
	def test_bug_9(self):
		p = parser.TransactionParser(parser.Lexer("@describe here as 'Large amounts of chalkdust lay all over the objects in this room, and a large chalkboard at one end has become coated with a thick layer of Queen Anne\\'s lace. Strange semi-phosphorescant orbs are piled all around this ancient hall.'"), self.wizard, self.exchange)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj_str, 'around')
		assert "\\" not in p.get_pobj_str('as')
	
	def test_inventory(self):
		self.box.set_location(self.wizard)
		
		p = parser.TransactionParser(parser.Lexer("drop my box"), self.wizard, self.exchange)
		self.failUnless(p.has_dobj())
		
		phil = self.exchange.get_object('phil')
		self.box.set_location(phil)
		
		p = parser.TransactionParser(parser.Lexer("take phil's box"), self.wizard, self.exchange)
		self.failUnless(p.has_dobj())
		
		# put it back for ther tests
		self.box.set_location(self.room)
