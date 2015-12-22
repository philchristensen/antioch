# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
# See LICENSE for details

import re

from twisted.trial import unittest
from twisted.internet import defer

from antioch import test
from antioch.core import exchange, interface, errors

exchange.ObjectExchange.permission_list = dict(
	anything   = 1,
	read       = 2,
	write      = 3,
	entrust    = 4,
	execute    = 5,
	move       = 6,
	transmute  = 7,
	derive     = 8,
	develop    = 9,
)

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
	
	def test_extract_id(self):
		self.failUnlessEqual(2, exchange.extract_id('#2 (Object)'))
		self.failUnlessEqual(2, exchange.extract_id(2))
		self.failUnlessEqual(2, exchange.extract_id('#2'))
		self.failUnlessEqual(None, exchange.extract_id('2'))
		self.failUnlessEqual(None, exchange.extract_id('Object'))
	
	def test_activate_default_grants(self):
		queries = [
			'',
			"INSERT INTO verb_name (name, verb_id) VALUES ('set_default_permissions', 1)",
			"INSERT INTO verb (ability, code, filename, id, method, origin_id, owner_id) VALUES ('f', '', '', DEFAULT, 'f', 1, NULL) RETURNING id",
			'SELECT * FROM verb WHERE id = 2048',
			"SELECT v.* FROM verb_name vn INNER JOIN verb v ON v.id = vn.verb_id WHERE vn.name = 'set_default_permissions' AND v.origin_id = 1",
			'SELECT * FROM object WHERE id = 1',
		]
		
		results = [
			[dict(id=1)],
			[dict(id=2048, origin_id=1, name='set_default_permissions')],
			[dict(id=2048, origin_id=1, name='set_default_permissions')],
			[dict(id=1, name='System Object')],
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
		
		pool = test.Anything(
			runQuery = runQuery,
			runOperation = runOperation,
		)
		
		ex = exchange.ObjectExchange(pool)
		ex.activate_default_grants()
		
		self.failUnlessEqual(ex.default_grants_active, True)
		self.failUnless('verb-2048' in ex.cache, "default permissions verb was not cached")
	
	def test_instantiate(self):
		results = [
			[dict(name='set_default_permissions', id=1, origin_id=1, method=True, code='pass')],
			[dict(name='set_default_permissions', id=1, origin_id=1, method=True, code='pass')],
			[dict(name='set_default_permissions', id=1, origin_id=1, method=True, code='pass')],
			[dict(name='set_default_permissions', id=1, origin_id=1, method=True, code='pass')],
			[dict(name='set_default_permissions', id=1, origin_id=1, method=True, code='pass')],
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
		ex = exchange.ObjectExchange(pool)
		
		obj = ex.instantiate('object', name="wizard", unique_name=True, default_permissions=False)
		self.failUnlessEqual(obj.get_name(real=True), 'wizard')
		
		obj2 = ex.instantiate('object', id=obj.get_id(), default_permissions=False)
		self.failUnless(obj == obj2)
	
	def test_mkobject(self):
		pool = test.Anything()
		ex = exchange.ObjectExchange(pool)
		
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
		ex = exchange.ObjectExchange(pool)
		
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
		ex = exchange.ObjectExchange(pool)
		
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
	def test_dequeue(self):
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
		
		self.queue_flushed = False
		def flush():
			self.queue_flushed = True
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		queue = test.Anything(flush=flush)
		ctx = test.Anything()
		ex = exchange.ObjectExchange(pool, queue, ctx)
		for index in range(1, 6):
			o = interface.Object(ex)
			o.set_id(index)
			ex.cache['object-%s' % index] = o
		
		yield ex.flush()
		
		self.failUnlessEqual(self.queue_flushed, True)
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
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		ex.save(o)
		
		self.failUnlessEqual(o.get_id(), 1024)
		
		o.set_name('test object', real=True)
		ex.save(o)
	
	def test_save_verb(self):
		expected_results = [False, [dict(id=1024)]]
		expected_query = """UPDATE verb 
							SET ability = 't', 
								code = '', 
								filename = NULL, 
								method = 'f', 
								origin_id = 0, 
								owner_id = NULL 
							WHERE id = 1024
							""".replace('\n', '').replace('\t', '')
		pool = test.Anything(
			runQuery		= lambda q, *a, **kw: expected_results.pop(),
			runOperation	= lambda q, *a, **kw: self.failUnlessEqual(q, expected_query)
		)
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		v = interface.Verb(o)
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
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		p = interface.Property(o)
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
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
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
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		o.set_name('test object', real=True)
		ex.cache['object-1024'] = o
		
		o2 = ex.get_object('#1024 (test object)')
		self.failUnless(o == o2)
		
		o3 = ex.get_object('#1024')
		self.failUnless(o2 == o3)
	
	def test_get_object_by_id(self):
		results = [[dict(id=1024)], [dict(id=1024)]]
		
		pool = test.Anything()
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		o.set_id(1024)
		ex.cache['object-1024'] = o
		
		o2 = ex.get_object(1024)
		self.failUnless(o == o2)
	
	def test_get_object_bad_key(self):
		pool = test.Anything()
		ex = exchange.ObjectExchange(pool)
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
		ex = exchange.ObjectExchange(pool)
		self.failUnlessRaises(errors.NoSuchObjectError, ex.get_object, "#2048")
		self.failUnlessRaises(errors.NoSuchObjectError, ex.get_object, 2048)
	
	def test_get_object_ambiguous_key(self):
		def runQuery(q, *a, **kw):
			self.failUnlessEquals(q, "SELECT * FROM object WHERE LOWER(name) = LOWER('ambiguous object name')")
			return [dict(id=1024), dict(id=2048)]
		
		pool = test.Anything(
			runQuery		= runQuery,
		)
		ex = exchange.ObjectExchange(pool)
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
		ex = exchange.ObjectExchange(pool)
		
		expected_ids = [1024, 2048, 4096]
		for obj_id in expected_ids:
			o = interface.Object(ex)
			o.set_id(obj_id)
			ex.cache['object-%s' % obj_id] = o
		
		expected_ids = expected_ids[1:]
		parents = ex.get_parents(1024)
		for parent in parents:
			expected_ids.remove(parent.get_id())
		self.failIf(expected_ids, "Didn't get back all the expected parent objects.")
	
	def test_has_parent(self):
		results = [
			[],
			[dict(id=2048)],
		]
		queries = [
			'SELECT parent_id AS id FROM object_relation WHERE child_id = 1024 ORDER BY weight DESC',
			'SELECT parent_id AS id FROM object_relation WHERE child_id = 1024 ORDER BY weight DESC',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	= runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		self.failUnlessEqual(ex.has_parent(1024, 2048), True)
		self.failUnlessEqual(ex.has_parent(1024, 4096), False)
	
	def test_has_verb(self):
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	= runQuery,
		)
		ex = exchange.ObjectExchange(pool)

		results = [
			[dict(id=1)],
			[dict(parent_id=2048)],
			[],
		]
		queries = [
			"SELECT v.id FROM verb v INNER JOIN verb_name vn ON v.id = vn.verb_id WHERE vn.name = 'look' AND v.origin_id = 2048",
			"SELECT parent_id FROM object_relation WHERE child_id = 1024",
			"SELECT v.id FROM verb v INNER JOIN verb_name vn ON v.id = vn.verb_id WHERE vn.name = 'look' AND v.origin_id = 1024",
		]
		self.failUnlessEqual(ex.has(1024, 'verb', 'look', recurse=True, unrestricted=True), True)
		
		results = [
			[],
		]
		queries = [
			'',
			"SELECT v.id FROM verb v INNER JOIN verb_name vn ON v.id = vn.verb_id WHERE vn.name = 'look' AND v.origin_id = 1024",
		]
		self.failUnlessEqual(ex.has(1024, 'verb', 'look', recurse=False, unrestricted=True), False)

		results = [
			[dict(id=2048)],
			[dict(id=1, origin_id=2048)],
			[dict(id=1)],
			[dict(parent_id=2048)],
			[],
		]
		queries = [
			'SELECT * FROM object WHERE id = 2048',
			'SELECT * FROM verb WHERE id = 1',
			"SELECT v.id FROM verb v INNER JOIN verb_name vn ON v.id = vn.verb_id WHERE vn.name = 'look' AND v.origin_id = 2048",
			"SELECT parent_id FROM object_relation WHERE child_id = 1024",
			"SELECT v.id FROM verb v INNER JOIN verb_name vn ON v.id = vn.verb_id WHERE vn.name = 'look' AND v.origin_id = 1024",
		]
		self.failUnlessEqual(ex.has(1024, 'verb', 'look', recurse=True, unrestricted=False), True)
		
		results = [
			[],
		]
		queries = [
			"SELECT v.id FROM verb v INNER JOIN verb_name vn ON v.id = vn.verb_id WHERE vn.name = 'look' AND v.origin_id = 1024",
		]
		self.failUnlessEqual(ex.has(1024, 'verb', 'look', recurse=False, unrestricted=False), False)
	
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
		ex = exchange.ObjectExchange(pool)
		
		expected_ids = [256, 512, 2048, 4096]
		for obj_id in expected_ids:
			o = interface.Object(ex)
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
		ex = exchange.ObjectExchange(pool)
		
		ex.remove_parent(1024, 2048)
	
	def test_add_parent(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(q, 'INSERT INTO object_relation (child_id, parent_id) VALUES (1024, 2048)')
		
		pool = test.Anything(
			runOperation		= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		
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
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		o.set_id(1024)
		v = interface.Verb(o)
		v.set_id(2048)
		
		ex.cache['object-1024'] = o
		ex.cache['verb-2048'] = v
		
		v2 = ex.get_verb(1024, 'look', recurse=False)
		self.failUnlessEqual(v2.get_id(), 2048)
		self.failUnlessEqual(v, v2)
	
	def test_get_verb_list(self):
		results = [
			[dict(id=1, names='one'), dict(id=2, names='two'), dict(id=3, names='three')]
		]
		
		queries = [
			'SELECT v.id, array_agg(vn.name) AS names FROM verb v INNER JOIN verb_name vn ON v.id = vn.verb_id WHERE v.origin_id = 1024 GROUP BY v.id',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		
		ex.get_verb_list(1024)
	
	def test_get_verb_names(self):
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(q, 'SELECT name FROM verb_name WHERE verb_id = 1024')
			return [dict(name='look')]
		
		pool = test.Anything(
			runQuery	= runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		
		ex.get_verb_names(1024)
	
	def test_add_verb_name(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(q, "INSERT INTO verb_name (name, verb_id) VALUES ('look', 1024)")
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		
		ex.add_verb_name(1024, 'look')
	
	def test_remove_verb_name(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(q, "DELETE FROM verb_name WHERE name = 'look' AND verb_id = 1024")
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		
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
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		o.set_id(512)
		v = interface.Verb(o)
		v.set_id(2048)
		
		o2 = interface.Object(ex)
		o2.set_id(1024)
		
		ex.cache['object-512'] = o
		ex.cache['object-1024'] = o2
		ex.cache['verb-2048'] = v
		
		v2 = ex.get_verb(1024, 'look', recurse=False)
		self.failUnlessEqual(v2, None)
		
		v2 = ex.get_verb(1024, 'look', recurse=True)
		self.failUnlessEqual(v2.get_id(), 2048)
		self.failUnlessEqual(v, v2)
	
	def test_get_ancestor_with(self):
		results = [
			[],
			[],
			[dict(id=2048, name='test object')],
			[dict(id=2048)],
			[dict(parent_id=2048)],
			[],
		]
		
		queries = [
			'SELECT parent_id FROM object_relation WHERE child_id = 2048',
			"SELECT p.id FROM property p WHERE p.name = 'name' AND p.origin_id = 2048",
			'SELECT * FROM object WHERE id = 2048',
			"SELECT v.origin_id AS id FROM verb v INNER JOIN verb_name vn ON v.id = vn.verb_id WHERE vn.name = 'look' AND v.origin_id = 2048",
			'SELECT parent_id FROM object_relation WHERE child_id = 1024',
			"SELECT v.origin_id AS id FROM verb v INNER JOIN verb_name vn ON v.id = vn.verb_id WHERE vn.name = 'look' AND v.origin_id = 1024",
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		
		o = ex.get_ancestor_with(1024, 'verb', 'look')
		self.failUnlessEqual(o.name, 'test object')
	
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
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		o.set_id(1024)
		p = interface.Property(o)
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
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		o.set_id(512)
		p = interface.Property(o)
		p.set_id(2048)
		
		o2 = interface.Object(ex)
		o2.set_id(1024)
		
		ex.cache['object-512'] = o
		ex.cache['object-1024'] = o2
		ex.cache['property-2048'] = p
		
		p2 = ex.get_property(1024, 'description', recurse=False)
		self.failUnlessEqual(p2, None)
		
		p2 = ex.get_property(1024, 'description', recurse=True)
		self.failUnlessEqual(p2.get_id(), 2048)
		self.failUnlessEqual(p, p2)
	
	def test_get_property_list(self):
		results = [
			[dict(id=1, name='one'), dict(id=2, name='two'), dict(id=3, name='three')]
		]
		
		queries = [
			'SELECT p.id, p.name FROM property p WHERE p.origin_id = 1024',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		
		ex.get_property_list(1024)
	
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
		ex = exchange.ObjectExchange(pool)
		
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
		ex = exchange.ObjectExchange(pool)
		
		self.failUnlessEqual(ex.is_unique_name('yet another name'), False)
		self.failUnlessEqual(ex.is_unique_name('some other name'), True)
		self.failUnlessEqual(ex.is_unique_name('some name'), False)
	
	def test_remove(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(q, "DELETE FROM object WHERE id = 1024")
		
		pool = test.Anything(
			runOperation	=	runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		
		ex.cache['object-1024'] = interface.Object(ex)
		ex.cache['object-1024'].set_id(1024)
		
		ex.remove('object', 1024)
		
		self.failUnlessEqual(ex.cache.get('object-1024'), None)
	
	def test_get_access(self):
		results = [
			[dict(permission_name='read'), dict(permission_name='write')],
			[dict(permission_name='read'), dict(permission_name='write')],
			[dict(permission_name='read'), dict(permission_name='write')],
		]
		
		queries = [
			'SELECT a.*, p.name AS permission_name FROM access a INNER JOIN permission p ON a.permission_id = p.id WHERE property_id = 1024 ORDER BY a.weight',
			'SELECT a.*, p.name AS permission_name FROM access a INNER JOIN permission p ON a.permission_id = p.id WHERE verb_id = 1024 ORDER BY a.weight',
			'SELECT a.*, p.name AS permission_name FROM access a INNER JOIN permission p ON a.permission_id = p.id WHERE object_id = 1024 ORDER BY a.weight',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		
		ex.get_access(1024, 'object')
		ex.get_access(1024, 'verb')
		ex.get_access(1024, 'property')
	
	def test_update_access(self):
		results = [
			[dict(id=4096)],
			[dict(id=2048)],
			[dict(id=2, name='write')],
			[dict(id=2, name='write')],
			[dict(id=1, name='read')],
			[dict(id=1, name='read')],
		]
		
		queries = [
			'',
			'DELETE FROM access WHERE id = 4096',
			'SELECT a.*, p.name AS permission FROM access a INNER JOIN permission p ON a.permission_id = p.id WHERE a.id = 4096',
			'DELETE FROM access WHERE id = 2048',
			'SELECT a.*, p.name AS permission FROM access a INNER JOIN permission p ON a.permission_id = p.id WHERE a.id = 2048',
			"INSERT INTO access (\"group\", accessor_id, object_id, permission_id, rule, type, weight) VALUES (NULL, 1024, 1024, 3, 'deny', 'accessor', 0)",
			# "SELECT p.* FROM permission p WHERE p.name = 'write'",
			"INSERT INTO access (\"group\", accessor_id, object_id, permission_id, rule, type, weight) VALUES (NULL, 1024, 1024, 3, 'allow', 'accessor', 0)",
			# "SELECT p.* FROM permission p WHERE p.name = 'write'",
			"INSERT INTO access (\"group\", accessor_id, object_id, permission_id, rule, type, weight) VALUES ('everyone', NULL, 1024, 2, 'deny', 'group', 0)",
			# "SELECT p.* FROM permission p WHERE p.name = 'read'",
			"INSERT INTO access (\"group\", accessor_id, object_id, permission_id, rule, type, weight) VALUES ('everyone', NULL, 1024, 2, 'allow', 'group', 0)",
			# "SELECT p.* FROM permission p WHERE p.name = 'read'",
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
		
		pool = test.Anything(
			runQuery		= runQuery,
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		o.set_id(1024)
		ex.cache['object-1024'] = o
		
		ex.update_access(0, 'allow', 'group', 'everyone', 'read', 0, o, False)
		ex.update_access(0, 'deny', 'group', 'everyone', 'read', 0, o, False)
		
		ex.update_access(0, 'allow', 'accessor', o, 'write', 0, o, False)
		ex.update_access(0, 'deny', 'accessor', o, 'write', 0, o, False)
		
		ex.update_access(2048, 'allow', 'accessor', o, 'write', 0, o, True)
		ex.update_access(4096, 'deny', 'accessor', o, 'write', 0, o, True)
	
	def test_is_allowed(self):
		results = [
			[],
			# [dict(id=1, name='anything')],
			# [dict(id=3, name='write')],
			[dict(rule='allow', type='group', group='everyone', permission_id=2)],
			# [dict(id=1, name='anything')],
			# [dict(id=2, name='read')],
		]
		
		queries = [
			'SELECT * FROM access WHERE object_id = 2048 AND permission_id IN (3, 1) AND property_id IS NULL AND verb_id IS NULL ORDER BY weight DESC',
			# "SELECT * FROM permission WHERE name = 'anything'",
			# "SELECT * FROM permission WHERE name = 'write'",
			'SELECT * FROM access WHERE object_id = 2048 AND permission_id IN (2, 1) AND property_id IS NULL AND verb_id IS NULL ORDER BY weight DESC',
			# "SELECT * FROM permission WHERE name = 'anything'",
			# "SELECT * FROM permission WHERE name = 'read'",
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		
		accessor = interface.Object(ex)
		accessor.set_id(1024)
		
		subject = interface.Object(ex)
		subject.set_id(2048)
		
		ex.cache['object-1024'] = accessor
		ex.cache['object-2048'] = subject
		
		self.failUnlessEqual(ex.is_allowed(accessor, 'read', subject), True)
		self.failUnlessEqual(ex.is_allowed(accessor, 'write', subject), False)
	
	def test_allow(self):
		results = [
			[dict(id=1, name='write')],
			[dict(id=1, name='anything')],
		]

		queries = [
			"INSERT INTO access (\"group\", accessor_id, object_id, permission_id, property_id, rule, type, verb_id, weight) VALUES (NULL, 0, 0, 3, NULL, 'allow', 'accessor', NULL, 0)",
			# "SELECT * FROM permission WHERE name = 'write'",
			"INSERT INTO access (\"group\", accessor_id, object_id, permission_id, property_id, rule, type, verb_id, weight) VALUES ('owners', NULL, 0, 1, NULL, 'allow', 'group', NULL, 0)",
			# "SELECT * FROM permission WHERE name = 'anything'",
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
		
		pool = test.Anything(
			runQuery		= runQuery,
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		o.allow('owners', 'anything')
		o.allow(o, 'write')
	
	def test_deny(self):
		results = [
			[dict(id=1, name='anything')],
		]

		queries = [
			"INSERT INTO access (\"group\", accessor_id, object_id, permission_id, property_id, rule, type, verb_id, weight) VALUES ('owners', NULL, 0, 1, NULL, 'deny', 'group', NULL, 0)",
			# "SELECT * FROM permission WHERE name = 'anything'",
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
		
		pool = test.Anything(
			runQuery		= runQuery,
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		
		o = interface.Object(ex)
		o.deny('owners', 'anything')
	
	def test_is_wizard(self):
		results = [
			[],
			[dict(id=1)],
		]
		
		queries = [
			"SELECT id FROM player WHERE wizard = 't' AND avatar_id = 1024",
			"SELECT id FROM player WHERE wizard = 't' AND avatar_id = 2048",
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		
		self.failUnlessEqual(ex.is_wizard(2048), True)
		self.failUnlessEqual(ex.is_wizard(1024), False)
	
	def test_is_connected_player(self):
		results = [
			[],
			[dict(connected=1)],
		]
		
		queries = [
			'SELECT 1 AS connected FROM player WHERE COALESCE(last_login, to_timestamp(0)) > COALESCE(last_logout, to_timestamp(0)) AND avatar_id = 1024',
			'SELECT 1 AS connected FROM player WHERE COALESCE(last_login, to_timestamp(0)) > COALESCE(last_logout, to_timestamp(0)) AND avatar_id = 2048',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		
		self.failUnlessEqual(ex.is_connected_player(2048), True)
		self.failUnlessEqual(ex.is_connected_player(1024), False)
	
	def test_set_player(self):
		results = [
			[dict(id=1)],
			[],
			[],
		]
		
		queries = [
			'DELETE FROM player WHERE avatar_id = 1',
			# 'SELECT id FROM player WHERE avatar_id = 1',
			"INSERT INTO player (avatar_id, crypt, wizard) VALUES (1, 'veYk4kGvM83ec', 't')",
			'SELECT id FROM player WHERE avatar_id = 1',
			"INSERT INTO player (avatar_id, crypt, wizard) VALUES (1, 'veFIEE6ItqLts', 'f')",
			'SELECT id FROM player WHERE avatar_id = 1',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
		
		pool = test.Anything(
			runQuery		= runQuery,
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		
		ex.set_player(1, True, False, 'password', test_salt='ve')
		ex.set_player(1, True, True, 'wizard password', test_salt='ve')
		ex.set_player(1, False)
	
	def test_validate_password(self):
		import crypt
		results = [
			[dict(crypt=crypt.crypt('password', 'ab'))],
			[dict(crypt=crypt.crypt('password', 'ab'))],
		]
		
		queries = [
			'SELECT crypt FROM player WHERE avatar_id = 1024',
			'SELECT crypt FROM player WHERE avatar_id = 1024'
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		
		self.failUnlessEqual(ex.validate_password(1024, 'password'), True)
		self.failUnlessEqual(ex.validate_password(1024, 'badpassword'), False)
	
	def test_register_task(self):
		queries = [
			"INSERT INTO task (args, delay, kwargs, origin_id, user_id, verb_name) VALUES ('[1,2,3]', 10, '{''a'':1,''b'':2}', '#1 (System Object)', 2, 'test') RETURNING id"
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return [dict(id=-1)]
		
		pool = test.Anything(
			runQuery	= runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		task_id = ex.register_task(2, 10, '#1 (System Object)', 'test', '[1,2,3]', "{'a':1,'b':2}")
		self.failUnlessEqual(task_id, -1)
	
	def test_get_tasks(self):
		queries = [
			'SELECT * FROM task WHERE user_id = 2',
			'SELECT * FROM task',
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
		
		pool = test.Anything(
			runQuery	= runQuery,
		)
		
		ex = exchange.ObjectExchange(pool)
		ex.get_tasks()
		ex.get_tasks(2)
	
	def test_get_task(self):
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), 'SELECT * FROM task WHERE id = -1')
			return [{'id':-1}]
		
		pool = test.Anything(
			runQuery	= runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		task = ex.get_task(-1)
		self.failUnlessEqual(task, {'id':-1})
	
	def test_get_aliases(self):
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), 'SELECT alias FROM object_alias WHERE object_id = -1')
			return [{'alias':'alias'}]
		
		pool = test.Anything(
			runQuery	= runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		aliases = ex.get_aliases(-1)
		self.failUnlessEqual(aliases, ['alias'])
	
	def test_add_alias(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), "INSERT INTO object_alias (alias, object_id) VALUES ('alias', -1)")
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		ex.add_alias(-1, 'alias')
	
	def test_remove_alias(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), "DELETE FROM object_alias WHERE alias = 'alias' AND object_id = -1")
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		ex.remove_alias(-1, 'alias')
	
	def test_get_observers(self):
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), 'SELECT o.* FROM object o INNER JOIN object_observer oo ON oo.observer_id = o.id WHERE oo.object_id = -1')
			return [{'id':-1}]
		
		pool = test.Anything(
			runQuery	= runQuery,
		)
		o = interface.Object('test')
		ex = exchange.ObjectExchange(pool)
		ex.cache['object--1'] = o
		observers = ex.get_observers(-1)
		self.failUnlessEqual(observers, [o])
	
	def test_add_observer(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), "INSERT INTO object_observer (object_id, observer_id) VALUES (-1, -2)")
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		ex.add_observer(-1, -2)
	
	def test_remove_observer(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), "DELETE FROM object_observer WHERE object_id = -1 AND observer_id = -2")
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		ex.remove_observer(-1, -2)
	
	def test_clear_observers(self):
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), "DELETE FROM object_observer WHERE object_id = -1")
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		ex.clear_observers(-1)
	
	def test_login_player(self):
		results = [
		]
		
		queries = [
			"UPDATE player SET last_login = now(), session_id = 'sid' WHERE avatar_id = 1024"
		]
		
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		
		ex.login_player(1024, 'sid')
	
	def test_logout_player(self):
		results = [
		]
		
		queries = [
			'UPDATE player SET last_logout = now() WHERE avatar_id = 1024'
		]
		
		def runOperation(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
		
		pool = test.Anything(
			runOperation	= runOperation,
		)
		ex = exchange.ObjectExchange(pool)
		
		ex.logout_player(1024)
	
	
	def test_is_player(self):
		results = [[dict(id=1024)], []]
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(q, "SELECT id FROM player WHERE avatar_id = 1024")
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		
		self.failUnlessEqual(ex.is_player(1024), False)
		self.failUnlessEqual(ex.is_player(1024), True)
	
	def test_find(self):
		results = [
			[dict(id=3)],
			[dict(id=2)],
			[dict(id=1)],
			[dict(id=3)],
			[dict(id=2)],
			[dict(id=1)],
			[],
			[],
			[],
		]
		
		queries = [
			'SELECT * FROM object WHERE id = 3',
			'SELECT * FROM object WHERE id = 2',
			'SELECT * FROM object WHERE id = 1',
			"SELECT o.id FROM object o INNER JOIN object_alias oa ON oa.object_id = o.id WHERE LOWER(oa.alias) = LOWER('box') AND o.location_id = 1024",
			"SELECT o.id FROM property p INNER JOIN object o ON p.origin_id = o.id WHERE p.name = 'name' AND LOWER(p.value) = LOWER('\"box\"') AND o.location_id = 1024",
			"SELECT id FROM object WHERE LOWER(name) = LOWER('box') AND location_id = 1024",
			"SELECT o.id FROM object o INNER JOIN object_alias oa ON oa.object_id = o.id WHERE LOWER(oa.alias) = LOWER('box') AND o.location_id = 1024",
			"SELECT o.id FROM property p INNER JOIN object o ON p.origin_id = o.id WHERE p.name = 'name' AND LOWER(p.value) = LOWER('\"box\"') AND o.location_id = 1024",
			"SELECT id FROM object WHERE LOWER(name) = LOWER('box') AND location_id = 1024",
		]
		
		def runQuery(q, *a, **kw):
			self.failUnlessEqual(rmws(q), queries.pop())
			return results.pop()
		
		pool = test.Anything(
			runQuery	=	runQuery,
		)
		ex = exchange.ObjectExchange(pool)
		
		self.failIf(ex.find(1024, 'box'))
		
		results = ex.find(1024, 'box')
		self.failUnlessEqual(len([x for x in results if x.get_id()]), 3)
	
	def test_get_contents(self):
		results = [
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
		ex = exchange.ObjectExchange(pool)
		
		expected_ids = [2048, 4096]
		for obj_id in expected_ids:
			o = interface.Object(ex)
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
		ex = exchange.ObjectExchange(pool)
		
		expected_ids = [256, 512, 2048, 4096]
		for obj_id in expected_ids:
			o = interface.Object(ex)
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
		ex = exchange.ObjectExchange(pool)
		
		expected_ids = [2048, 4096]
		for obj_id in expected_ids:
			o = interface.Object(ex)
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
		ex = exchange.ObjectExchange(pool)
		
		expected_ids = [256, 512, 2048, 4096]
		for obj_id in expected_ids:
			o = interface.Object(ex)
			o.set_id(obj_id)
			ex.cache['object-%s' % obj_id] = o
		
		self.failUnlessEqual(ex.contains(1024, 256, recurse=True), True)
		self.failUnlessEqual(ex.contains(1024, 512, recurse=True), True)
		self.failUnlessEqual(ex.contains(1024, 2048, recurse=True), True)
		self.failUnlessEqual(ex.contains(1024, 4096, recurse=True), True)
	
	
	