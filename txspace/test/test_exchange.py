# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

import re

from twisted.trial import unittest
from twisted.internet import defer

from txspace import exchange, test, model, errors

def rmws(q):
	return re.sub(r'\s+', ' ', q).strip()

def printQuery(func):
	def f(q, *a, **kw):
		print (rmws(q), a, kw)
		return func(q, *a, **kw)
	return f

class ObjectExchangeTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_instantiate(self):
		results = [
			[dict(name='set_default_permissions', id=1, origin_id=1, method=True)],
			[dict(name='System Object', id=1)],
			[dict(name='set_default_permissions', id=1, origin_id=1, method=True)],
			[dict(name='wizard', id=2)],
		]
		def runQuery(query, *a, **kw):
			if(query.startswith('SELECT')):
				return results.pop()
			else:
				expected_insert = """INSERT INTO object 
										(id, location_id, name, owner_id, unique_name) 
									VALUES 
										(DEFAULT, NULL, 'wizard', NULL, 't') 
									RETURNING id
								""".replace('\t', '').replace('\n', '')
				self.failUnlessEqual(query, expected_insert)
				return [dict(id=1)]
		
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ctx = test.Anything(
			get_type	= lambda:'object',
			is_allowed	= lambda s, p: True,
		)
		ex = exchange.ObjectExchange(pool, ctx)
		
		obj = ex.new(name="wizard", unique_name=True)
		self.failUnlessEqual(obj.get_name(real=True), 'wizard')
		
		obj2 = ex.instantiate('object', id=obj.get_id())
		self.failUnless(obj == obj2)
	
	def test_mkobject(self):
		pool = test.Anything()
		ctx = test.Anything(
			get_type	= lambda:'object',
			is_allowed	= lambda s, p: True,
		)
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = ex._mkobject(dict(
			name		= 'Test Object',
			unique_name	= False,
			owner_id	= 1024,
			location_id	= 2048,
		))
		
		self.failUnlessEqual(o.get_name(real=True), 'Test Object')
		self.failUnlessEqual(o._owner_id, 1024)
		self.failUnlessEqual(o._location_id, 2048)
	
	def test_mkverb(self):
		def runQuery(query, *a, **kw):
			if(query.lower().startswith('select')):
				return [dict(name='Origin', id=1024)]
			else:
				print query
		
		pool = test.Anything(
			runQuery	= runQuery,
		)
		ctx = test.Anything(
			get_type	= lambda:'object',
			is_allowed	= lambda s, p: True,
		)
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = ex._mkobject(dict(
			name		= 'Test Object',
			unique_name	= False,
			owner_id	= 1024,
			location_id	= 2048,
		))
		o.set_id(1024)
		ex.cache['object-1024'] = o
		
		v = ex._mkverb(dict(
			code		= 'caller.write("Hello, World!")',
			origin_id	= 1024,
			owner_id	= 2048,
			ability		= True,
			method		= False,
		))
		
		self.failUnlessEqual(v.get_code(), 'caller.write("Hello, World!")')
		self.failUnlessEqual(v._origin_id, 1024)
		self.failUnlessEqual(v._owner_id, 2048)
		self.failUnlessEqual(v.is_ability(), True)
		self.failUnlessEqual(v.is_method(), False)
	
	def test_mkproperty(self):
		def runQuery(query, *a, **kw):
			return [dict(name='Origin', id=1024)]
		
		pool = test.Anything(
			runQuery	= runQuery,
		)
		ctx = test.Anything(
			get_type	= lambda:'object',
			is_allowed	= lambda s, p: True,
		)
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = ex._mkobject(dict(
			name		= 'Test Object',
			unique_name	= False,
			owner_id	= 1024,
			location_id	= 2048,
		))
		o.set_id(1024)
		ex.cache['object-1024'] = o
		
		p = ex._mkproperty(dict(
			name		= 'my property',
			value		= 'some random string',
			origin_id	= 1024,
			owner_id	= 2048,
			type		= 'string',
		))
		
		self.failUnlessEqual(p.get_name(), 'my property')
		self.failUnlessEqual(p._origin_id, 1024)
		self.failUnlessEqual(p._owner_id, 2048)
		self.failUnlessEqual(p._type, 'string')
	
	@defer.inlineCallbacks
	def test_commit(self):
		ids = list(range(1, 6))
		
		queries = [
			"UPDATE object SET location_id = NULL, name = '', owner_id = NULL, unique_name = 'f' WHERE id = 6",
			"UPDATE object SET location_id = NULL, name = '', owner_id = NULL, unique_name = 'f' WHERE id = 5",
			"UPDATE object SET location_id = NULL, name = '', owner_id = NULL, unique_name = 'f' WHERE id = 4",
			"UPDATE object SET location_id = NULL, name = '', owner_id = NULL, unique_name = 'f' WHERE id = 3",
			"UPDATE object SET location_id = NULL, name = '', owner_id = NULL, unique_name = 'f' WHERE id = 2",
			"UPDATE object SET location_id = NULL, name = '', owner_id = NULL, unique_name = 'f' WHERE id = 1",
		]
		
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(q, queries.pop())
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ctx = test.Anything()
		queue = test.Anything(commit=lambda: defer.Deferred().callback(None))
		ex = exchange.ObjectExchange(pool, queue, ctx)
		for index in range(1, 6):
			o = model.Object(ex)
			o.set_id(index)
			ex.cache['object-%s' % index] = o
		
		yield ex.commit()
		
		self.failUnlessEqual(ex.cache, {})
	
	def test_save_object(self):
		expected_results = [False, [dict(id=1024)]]
		expected_query = """UPDATE object 
							SET location_id = NULL, 
								name = 'test object', 
								owner_id = NULL, 
								unique_name = 'f' 
							WHERE id = 1024
							""".replace('\n', '').replace('\t', '')
		pool = test.Anything(
			runQuery		= lambda q: expected_results.pop(),
			runOperation	= lambda q: self.failUnlessEqual(q, expected_query)
		)
		ctx = test.Anything(
			get_type	= lambda:'object',
			is_allowed	= lambda s, p: True,
		)
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = model.Object(ex)
		ex.save(o)
		
		self.failUnlessEqual(o.get_id(), 1024)
		
		o.set_name('test object', real=True)
		ex.save(o)
	
	def test_save_verb(self):
		expected_results = [False, [dict(id=1024)]]
		expected_query = """UPDATE verb 
							SET ability = 't', 
								code = '', 
								method = 'f', 
								origin_id = 0, 
								owner_id = NULL 
							WHERE id = 1024
							""".replace('\n', '').replace('\t', '')
		pool = test.Anything(
			runQuery		= lambda q, *a, **kw: expected_results.pop(),
			runOperation	= lambda q, *a, **kw: self.failUnlessEqual(q, expected_query)
		)
		ctx = test.Anything(
			get_type	= lambda:'object',
			is_allowed	= lambda s, p: True,
		)
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = model.Object(ex)
		v = model.Verb(o)
		ex.save(v)
		
		self.failUnlessEqual(v.get_id(), 1024)
		
		v.set_ability(True)
		ex.save(v)
	
	def test_save_property(self):
		expected_results = [False, [dict(id=1024)]]
		expected_query = """UPDATE property 
							SET name = 'myprop', 
								origin_id = 0, 
								owner_id = NULL, 
								type = 'string', 
								value = NULL 
							WHERE id = 1024
							""".replace('\n', '').replace('\t', '')
		pool = test.Anything(
			runQuery		= lambda q, *a, **kw: expected_results.pop(),
			runOperation	= lambda q, *a, **kw: self.failUnlessEqual(q, expected_query)
		)
		ctx = test.Anything(
			get_type	= lambda:'object',
			is_allowed	= lambda s, p: True,
		)
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = model.Object(ex)
		p = model.Property(o)
		ex.save(p)
		
		self.failUnlessEqual(p.get_id(), 1024)
		
		p.set_name('myprop')
		ex.save(p)
		
		self.failUnlessEqual(p.get_name(), 'myprop')
	
	def test_get_object_by_name(self):
		results = [[dict(id=1024)], [dict(id=1024)], False]
		queries = [
			"SELECT * FROM object WHERE LOWER(name) = LOWER('test object')",
			"INSERT INTO object (id, location_id, name, owner_id, unique_name) VALUES (DEFAULT, NULL, 'test object', NULL, 'f') RETURNING id",
			"SELECT * FROM object WHERE LOWER(name) = LOWER('test object') AND unique_name = 't'",
		]
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(q, queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ctx = test.Anything(
			get_type	= lambda:'object',
			is_allowed	= lambda p, s: True,
		)
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = model.Object(ex)
		o.set_name('test object', real=True)
		ex.cache['object-1024'] = o
		
		o2 = ex.get_object('test object')
		self.failUnless(o == o2)
	
	def test_get_object_by_id_str(self):
		results = [[dict(id=1024)], [dict(id=1024)], [dict(id=1024)], False]
		
		queries = [
			"INSERT INTO object (id, location_id, name, owner_id, unique_name) VALUES (DEFAULT, NULL, 'test object', NULL, 'f') RETURNING id",
			"SELECT * FROM object WHERE LOWER(name) = LOWER('test object') AND unique_name = 't'",
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(q, queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ctx = test.Anything(
			get_type	= lambda:'object',
			is_allowed	= lambda p, s: True,
		)
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = model.Object(ex)
		o.set_name('test object', real=True)
		ex.cache['object-1024'] = o
		
		o2 = ex.get_object('#1024 (test object)')
		self.failUnless(o == o2)
		
		o3 = ex.get_object('#1024')
		self.failUnless(o2 == o3)
	
	def test_get_object_by_id(self):
		results = [[dict(id=1024)], [dict(id=1024)]]
		
		pool = test.Anything()
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = model.Object(ex)
		o.set_id(1024)
		ex.cache['object-1024'] = o
		
		o2 = ex.get_object(1024)
		self.failUnless(o == o2)
	
	def test_get_object_bad_key(self):
		pool = test.Anything()
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		self.failUnlessRaises(ValueError, ex.get_object, None)
	
	def test_get_object_unknown_key(self):
		queries = [
			'SELECT * FROM object WHERE id = 2048',
			'SELECT * FROM object WHERE id = 2048',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEquals(q, queries.pop())
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		self.failUnlessRaises(errors.NoSuchObjectError, ex.get_object, "#2048")
		self.failUnlessRaises(errors.NoSuchObjectError, ex.get_object, 2048)
	
	def test_get_object_ambiguous_key(self):
		def runQuery(q, *a, **kw):
			self.failUnlessEquals(q, "SELECT * FROM object WHERE LOWER(name) = LOWER('ambiguous object name')")
			return [dict(id=1024), dict(id=2048)]
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		self.failUnlessRaises(errors.AmbiguousObjectError, ex.get_object, "ambiguous object name")
	
	def test_get_parents(self):
		results = [
			[dict(id=4096), dict(id=2048)],
		]
		queries = [
			'SELECT parent_id AS id FROM object_relation WHERE child_id = 1024 ORDER BY weight DESC',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		expected_ids = [1024, 2048, 4096]
		for obj_id in expected_ids:
			o = model.Object(ex)
			o.set_id(obj_id)
			ex.cache['object-%s' % obj_id] = o
		
		expected_ids = expected_ids[1:]
		parents = ex.get_parents(1024)
		for parent in parents:
			expected_ids.remove(parent.get_id())
		self.failIf(expected_ids, "Didn't get back all the expected parent objects.")
	
	def test_get_all_parents(self):
		results = [
			[dict(id=256)],
			[dict(id=512)],
			[dict(id=2048)],
			[dict(id=4096)],
			[], 
			[dict(id=512), dict(id=256)], 
			[dict(id=4096), dict(id=2048)],
		]

		queries = [
			'SELECT parent_id AS id FROM object_relation WHERE child_id IN (512,256) ORDER BY weight DESC',
			'SELECT parent_id AS id FROM object_relation WHERE child_id IN (4096,2048) ORDER BY weight DESC',
			'SELECT parent_id AS id FROM object_relation WHERE child_id = 1024 ORDER BY weight DESC',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		expected_ids = [256, 512, 2048, 4096]
		for obj_id in expected_ids:
			o = model.Object(ex)
			o.set_id(obj_id)
			ex.cache['object-%s' % obj_id] = o
		
		parents = ex.get_parents(1024, recurse=True)
		for parent in parents:
			expected_ids.remove(parent.get_id())
		self.failIf(expected_ids, "Didn't get back all the expected parent objects.")
	
	def test_remove_parent(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(q, 'DELETE FROM object_relation WHERE child_id = 1024 AND parent_id = 2048')
		
		pool = test.Anything(
			runOperation		= runOperation,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		ex.remove_parent(1024, 2048)
	
	def test_add_parent(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(q, 'INSERT INTO object_relation (child_id, parent_id) VALUES (1024, 2048)')
		
		pool = test.Anything(
			runOperation		= runOperation,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		ex.add_parent(1024, 2048)
	
	def test_get_verb(self):
		results = [
			[dict(id=1024)],
			[dict(id=2048, origin_id=1024)],
			[dict(id=2048)],
		]
		
		queries = [
			"SELECT v.* FROM verb v INNER JOIN verb_name vn ON vn.verb_id = v.id WHERE vn.name = 'look' AND v.origin_id = 1024",
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = model.Object(ex)
		o.set_id(1024)
		v = model.Verb(o)
		v.set_id(2048)
		
		ex.cache['object-1024'] = o
		ex.cache['verb-2048'] = v
		
		v2 = ex.get_verb(1024, 'look', recurse=False)
		self.failUnlessEqual(v2.get_id(), 2048)
		self.failUnlessEqual(v, v2)
	
	def test_get_verb_names(self):
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(q, 'SELECT name FROM verb_name WHERE verb_id = 1024')
			return [dict(name='look')]
		
		pool = test.Anything(
			runQuery	= runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		ex.get_verb_names(1024)
	
	def test_add_verb_name(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(q, "INSERT INTO verb_name (name, verb_id) VALUES ('look', 1024)")
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		ex.add_verb_name(1024, 'look')
	
	def test_remove_verb_name(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(q, "DELETE FROM verb_name WHERE name = 'look' AND verb_id = 1024")
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		ex.remove_verb_name(1024, 'look')
	
	def test_get_ancestor_verb(self):
		results = [
			[dict(id=2048, origin_id=1024)],
			[dict(parent_id=512)],
			[],
			[],
		]
		
		queries = [
			"SELECT v.* FROM verb v INNER JOIN verb_name vn ON vn.verb_id = v.id WHERE vn.name = 'look' AND v.origin_id = 512",
			'SELECT parent_id FROM object_relation WHERE child_id = 1024',
			"SELECT v.* FROM verb v INNER JOIN verb_name vn ON vn.verb_id = v.id WHERE vn.name = 'look' AND v.origin_id = 1024",
			"SELECT v.* FROM verb v INNER JOIN verb_name vn ON vn.verb_id = v.id WHERE vn.name = 'look' AND v.origin_id = 1024",
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = model.Object(ex)
		o.set_id(512)
		v = model.Verb(o)
		v.set_id(2048)
		
		o2 = model.Object(ex)
		o2.set_id(1024)
		
		ex.cache['object-512'] = o
		ex.cache['object-1024'] = o2
		ex.cache['verb-2048'] = v
		
		v2 = ex.get_verb(1024, 'look', recurse=False)
		self.failUnlessEqual(v2, None)
		
		v2 = ex.get_verb(1024, 'look', recurse=True)
		self.failUnlessEqual(v2.get_id(), 2048)
		self.failUnlessEqual(v, v2)
	
	def test_get_property(self):
		results = [
			[dict(id=1024)],
			[dict(id=2048, origin_id=1024)],
			[dict(id=2048)],
		]
		pool = test.Anything(
			runQuery		= lambda *a, **kw: results.pop(),
			runOperation	= lambda q, *a, **kw:
				self.failUnlessEqual(q, "UPDATE property SET name = 'description', origin_id = 1024, owner_id = NULL, type = 'string', value = NULL WHERE id = 2048")
		)
		ctx = test.Anything(
			get_type	= lambda:'object',
			is_allowed	= lambda s,p: True,
		)
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = model.Object(ex)
		o.set_id(1024)
		p = model.Property(o)
		p.set_id(2048)
		p.set_name('description')
		
		ex.cache['object-1024'] = o
		ex.cache['property-2048'] = p
		
		p2 = ex.get_property(1024, 'description', recurse=False)
		self.failUnlessEqual(p2.get_id(), 2048)
		self.failUnlessEqual(p, p2)
	
	def test_get_ancestor_property(self):
		results = [
			[dict(id=2048, origin_id=1024, name='description')],
			[dict(id=2048, origin_id=1024)],
			[dict(parent_id=512)],
			[],
			[],
		]
		pool = test.Anything(
			runQuery	=	lambda *a, **kw: results.pop(),
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		o = model.Object(ex)
		o.set_id(512)
		p = model.Property(o)
		p.set_id(2048)
		
		o2 = model.Object(ex)
		o2.set_id(1024)
		
		ex.cache['object-512'] = o
		ex.cache['object-1024'] = o2
		ex.cache['property-2048'] = p
		
		p2 = ex.get_property(1024, 'description', recurse=False)
		self.failUnlessEqual(p2, None)
		
		p2 = ex.get_property(1024, 'description', recurse=True)
		self.failUnlessEqual(p2.get_id(), 2048)
		self.failUnlessEqual(p, p2)
	
	def test_refs(self):
		names = ['some name', 'some other name', 'yet another name']
		results = [10, 1, 0]
		def runQuery(q, *a, **kw):
			count = results.pop()
			self.failUnlessEqual(q, "SELECT COUNT(*) AS count FROM object WHERE name = '%s'" % names.pop())
			return [dict(count=count)]
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		self.failUnlessEqual(ex.refs('yet another name'), 0)
		self.failUnlessEqual(ex.refs('some other name'), 1)
		self.failUnlessEqual(ex.refs('some name'), 10)
	
	def test_is_unique_name(self):
		names = ['some name', 'some other name', 'yet another name']
		results = [False, True, False]
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(q, "SELECT * FROM object WHERE LOWER(name) = LOWER('%s') AND unique_name = 't'" % names.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		self.failUnlessEqual(ex.is_unique_name('yet another name'), False)
		self.failUnlessEqual(ex.is_unique_name('some other name'), True)
		self.failUnlessEqual(ex.is_unique_name('some name'), False)
	
	def test_remove(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(q, "DELETE FROM object WHERE id = 1024")
		
		pool = test.Anything(
			runOperation	=	runOperation,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		ex.cache['object-1024'] = model.Object(ex)
		ex.cache['object-1024'].set_id(1024)
		
		ex.remove('object', 1024)
		
		self.failUnlessEqual(ex.cache.get('object-1024'), None)
	
	def test_is_player(self):
		results = [[dict(id=1024)], []]
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(q, "SELECT id FROM player WHERE avatar_id = 1024")
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		self.failUnlessEqual(ex.is_player(1024), False)
		self.failUnlessEqual(ex.is_player(1024), True)
	
	def test_get_contents(self):
		results = [
			# [dict(id=2048)],
			# [dict(id=4096)],
			[], 
			[dict(id=4096), dict(id=2048)],
		]
		
		queries = [
			'SELECT parent_id FROM object_relation WHERE child_id = 4096',
			'SELECT p.* FROM property p WHERE p.name = 0 AND p.origin_id = 4096',
			'SELECT id FROM object WHERE location_id = 1024',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		expected_ids = [2048, 4096]
		for obj_id in expected_ids:
			o = model.Object(ex)
			o.set_id(obj_id)
			ex.cache['object-%s' % obj_id] = o
		
		contents = ex.get_contents(1024)
		for content in contents:
			expected_ids.remove(content.get_id())
		self.failIf(expected_ids, "Didn't get back all the expected content objects.")
	
	def test_get_all_contents(self):
		results = [
			[dict(id=256)],
			[dict(id=512)],
			[dict(id=2048)],
			[dict(id=4096)],
			[], 
			[dict(id=512), dict(id=256)], 
			[dict(id=4096), dict(id=2048)],
		]

		queries = [
			'SELECT id FROM object WHERE location_id IN (512,256)',
			'SELECT id FROM object WHERE location_id IN (4096,2048)',
			'SELECT id FROM object WHERE location_id = 1024',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		expected_ids = [256, 512, 2048, 4096]
		for obj_id in expected_ids:
			o = model.Object(ex)
			o.set_id(obj_id)
			ex.cache['object-%s' % obj_id] = o
		
		contents = ex.get_contents(1024, recurse=True)
		for content in contents:
			expected_ids.remove(content.get_id())
		self.failIf(expected_ids, "Didn't get back all the expected content objects.")
	
	def test_contains(self):
		results = [
			[dict(id=4096), dict(id=2048)],
			[dict(id=2048), dict(id=4096)],
		]
		
		queries = [
			'SELECT id FROM object WHERE location_id = 1024 ORDER BY CASE WHEN id = 4096 THEN 0 ELSE 1 END',
			'SELECT id FROM object WHERE location_id = 1024 ORDER BY CASE WHEN id = 2048 THEN 0 ELSE 1 END',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		expected_ids = [2048, 4096]
		for obj_id in expected_ids:
			o = model.Object(ex)
			o.set_id(obj_id)
			ex.cache['object-%s' % obj_id] = o
		
		self.failUnlessEqual(ex.contains(1024, 2048), True)
		self.failUnlessEqual(ex.contains(1024, 4096), True)
	
	def test_contains_recursive(self):
		results = [
			[dict(id=4096), dict(id=2048)],
			[dict(id=2048), dict(id=4096)],
			[dict(id=512), dict(id=256)],
			[dict(id=4096), dict(id=2048)],
			[dict(id=256), dict(id=512)],
			[dict(id=4096), dict(id=2048)],
		]

		queries = [
			'SELECT id FROM object WHERE location_id = 1024 ORDER BY CASE WHEN id = 4096 THEN 0 ELSE 1 END',
			'SELECT id FROM object WHERE location_id = 1024 ORDER BY CASE WHEN id = 2048 THEN 0 ELSE 1 END',
			'SELECT id FROM object WHERE location_id IN (4096,2048) ORDER BY CASE WHEN id = 512 THEN 0 ELSE 1 END',
			'SELECT id FROM object WHERE location_id = 1024 ORDER BY CASE WHEN id = 512 THEN 0 ELSE 1 END',
			'SELECT id FROM object WHERE location_id IN (4096,2048) ORDER BY CASE WHEN id = 256 THEN 0 ELSE 1 END',
			'SELECT id FROM object WHERE location_id = 1024 ORDER BY CASE WHEN id = 256 THEN 0 ELSE 1 END',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, ctx)
		
		expected_ids = [256, 512, 2048, 4096]
		for obj_id in expected_ids:
			o = model.Object(ex)
			o.set_id(obj_id)
			ex.cache['object-%s' % obj_id] = o
		
		self.failUnlessEqual(ex.contains(1024, 256, recurse=True), True)
		self.failUnlessEqual(ex.contains(1024, 512, recurse=True), True)
		self.failUnlessEqual(ex.contains(1024, 2048, recurse=True), True)
		self.failUnlessEqual(ex.contains(1024, 4096, recurse=True), True)
	
	
	