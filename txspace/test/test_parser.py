# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

import sys, os, os.path, time

from twisted.internet import reactor
from twisted.trial import unittest

from txspace import parser, errors, bootstrap, exchange, dbapi, assets, transact, test

psql_path = 'psql'

initialized = False
pool = None

# dbapi.debug = True

def init_database():
	global initialized, pool, oscar
	if(initialized):
		return pool
	initialized = True
	
	db_url = transact.db_url.split('/')
	db_url[-1] = 'txspace_test'
	db_url = '/'.join(db_url)
	
	bootstrap.initialize_database(psql_path, db_url)
	
	schema_path = assets.get('bootstraps/test/database-schema.sql')
	bootstrap.load_schema(psql_path, db_url, schema_path)
	
	pool = dbapi.connect(db_url)
	bootstrap_path = assets.get('bootstraps/test/database-bootstrap.py')
	bootstrap.load_python(pool, bootstrap_path)

	return pool

class ParserTestCase(unittest.TestCase):
	def setUp(self):
		self.pool = init_database()
		self.exchange = exchange.ObjectExchange(self.pool)
		self.queue = test.Anything()
		
		self.wizard = self.exchange.get_object("Wizard")
		self.box = self.exchange.get_object("box")
		self.room = self.exchange.get_object("The Laboratory")
	
	def tearDown(self):
		self.exchange.commit()
		
		self.wizard = None
		self.box = None
		self.room = None
	
	def test_parse_verb(self):
		p = parser.TransactionParser(parser.Lexer("look"), self.wizard, self.exchange, self.queue)
		assert not p.has_dobj(), "unexpected object found for dobj"
		assert not p.has_dobj_str(), "unexpected string found for dobj"
		assert not p.prepositions, "unexpected prepositional objects found"
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "on")
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj_str)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj_str, "on")
	
	def test_parse_verb_dobj(self):
		p = parser.TransactionParser(parser.Lexer("look wizard"), self.wizard, self.exchange, self.queue)
		assert p.has_dobj(), "dobj 'wizard' not found"
		assert p.has_dobj_str(), "dobj string 'wizard' not found"
		assert not p.prepositions, "unexpected prepositional objects/strings found"
		self.assertEqual(p.get_dobj(), self.wizard)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "on")
		self.assertEqual(p.get_dobj_str().lower(), self.wizard.get_name().lower())
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj_str, "on")
		
	def test_parse_verb_pobj(self):
		p = parser.TransactionParser(parser.Lexer("look through peephole"), self.wizard, self.exchange, self.queue)
		assert not p.has_dobj(), "unexpected object found for dobj"
		assert not p.has_dobj_str(), "unexpected string found for dobj"
		assert p.has_pobj_str('through'), "no prepositional object string found for 'through'"
		assert not p.has_pobj('through'), "no prepositional object found for 'through'"
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchObjectError, p.get_pobj, "through")
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj_str)
		self.assertEqual(p.get_pobj_str("through"), "peephole")
		
	def test_parse_verb_pobj_pobj(self):
		p = parser.TransactionParser(parser.Lexer("look through peephole with box"), self.wizard, self.exchange, self.queue)
		assert not p.has_dobj(), "unexpected object found for dobj"
		assert not p.has_dobj_str(), "unexpected string found for dobj"
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "from")
		self.assertEqual(p.get_pobj("with"), self.box)
		self.assertEqual(p.get_pobj_str("with"), "box")
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj_str)
		self.assertEqual(p.get_pobj_str("through"), "peephole")
	
	def test_parse_verb_dobj_pobj(self):
		p = parser.TransactionParser(parser.Lexer("take glasses from wizard with tongs"), self.wizard, self.exchange, self.queue)
		self.assertRaises(errors.NoSuchObjectError, p.get_dobj)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj, "under")
		self.assertEqual(p.get_dobj_str(), "glasses")
		self.assertEqual(p.get_pobj_str("with"), "tongs")
		self.assertEqual(p.get_pobj("from"), self.wizard)
		self.assertEqual(p.get_pobj_str("from"), "wizard")
	
	def test_complex(self):
		p = parser.TransactionParser(parser.Lexer("take the box from 'bag under stairs' with tongs in wizard's bag"), self.wizard, self.exchange, self.queue)
		self.assertRaises(errors.NoSuchObjectError, p.get_pobj, "from")
		self.assertRaises(errors.NoSuchObjectError, p.get_pobj, "with")
		self.assertEqual(p.get_pobj_str('from'), 'bag under stairs')
		self.assertEqual(p.get_dobj(), self.box)
		self.assertEqual(p.get_pobj_str("with"), "tongs")
	
	def test_quoted_strings(self):
		p = parser.TransactionParser(parser.Lexer("@passwd wizard to 'something here'"), self.wizard, self.exchange, self.queue)
		self.assertEqual(p.get_pobj_str('to'), 'something here')
	
	def test_bug_9(self):
		p = parser.TransactionParser(parser.Lexer("@describe here as 'Large amounts of chalkdust lay all over the objects in this room, and a large chalkboard at one end has become coated with a thick layer of Queen Anne\\'s lace. Strange semi-phosphorescant orbs are piled all around this ancient hall.'"), self.wizard, self.exchange, self.queue)
		self.assertRaises(errors.NoSuchPrepositionError, p.get_pobj_str, 'around')
		assert "\\" not in p.get_pobj_str('as')
	
	def test_inventory(self):
		self.box.set_location(self.wizard)
		
		p = parser.TransactionParser(parser.Lexer("drop my box"), self.wizard, self.exchange, self.queue)
		self.failUnless(p.has_dobj())
		
		phil = self.exchange.get_object('phil')
		self.box.set_location(phil)
		
		p = parser.TransactionParser(parser.Lexer("take phil's box"), self.wizard, self.exchange, self.queue)
		self.failUnless(p.has_dobj())
		
		# put it back for ther tests
		self.box.set_location(self.room)
