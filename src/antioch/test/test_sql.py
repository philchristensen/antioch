# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest

from antioch.util import sql

class SQLTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_interp_args_1(self):
		query = sql.interp("SELECT * FROM some_table WHERE a = %s AND b = %s", 1, 'something')
		expecting = "SELECT * FROM some_table WHERE a = %s AND b = %s" % (1, repr('something'))
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_interp_args_list(self):
		query = sql.interp("SELECT * FROM some_table WHERE a IN %s AND b = %s", [1,2,3], 'something')
		expecting = "SELECT * FROM some_table WHERE a IN (1,2,3) AND b = 'something'"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_delete(self):
		query = sql.build_delete('table', {'col1':'col1_data', 'col2':'col2_data'});
		expecting = "DELETE FROM table WHERE col1 = 'col1_data' AND col2 = 'col2_data'"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_delete2(self):
		query = sql.build_delete('table', col1='col1_data', col2='col2_data');
		expecting = "DELETE FROM table WHERE col1 = 'col1_data' AND col2 = 'col2_data'"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_insert(self):
		query = sql.build_insert('table', {'col2':'col2_data', 'col1':sql.RAW("ENCRYPT('something')")});
		expecting = "INSERT INTO table (col1, col2) VALUES (ENCRYPT('something'), 'col2_data')"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_insert2(self):
		query = sql.build_insert('table', col2='col2_data', col1=sql.RAW("ENCRYPT('something')"));
		expecting = "INSERT INTO table (col1, col2) VALUES (ENCRYPT('something'), 'col2_data')"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_multiple_insert(self):
		query = sql.build_insert('table', [{'col2':'col2_data', 'col1':sql.RAW("ENCRYPT('something')")}, {'col2':'col2_data', 'col1':sql.RAW("ENCRYPT('something')")}]);
		expecting = "INSERT INTO table (col1, col2) VALUES (ENCRYPT('something'), 'col2_data'), (ENCRYPT('something'), 'col2_data')"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_insert_dot_syntax(self):
		query = sql.build_insert('db.table', {'col2':'col2_data', 'col1':sql.RAW("ENCRYPT('something')")});
		expecting = "INSERT INTO db.table (col1, col2) VALUES (ENCRYPT('something'), 'col2_data')"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_insert_raw(self):
		query = sql.build_insert('table', {'col2':'col2_data', 'col1':'col1_data'});
		expecting = "INSERT INTO table (col1, col2) VALUES ('col1_data', 'col2_data')"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_dot_syntax(self):
		query = sql.build_select('db.table', {'t.col2':'col2_data', 's.col1':'col1_data'});
		expecting = "SELECT * FROM db.table WHERE s.col1 = 'col1_data' AND t.col2 = 'col2_data'"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select(self):
		query = sql.build_select('table', {'col2':'col2_data', 'col1':'col1_data'});
		expecting = "SELECT * FROM table WHERE col1 = 'col1_data' AND col2 = 'col2_data'"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select2(self):
		query = sql.build_select('table', col2='col2_data', col1='col1_data');
		expecting = "SELECT * FROM table WHERE col1 = 'col1_data' AND col2 = 'col2_data'"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_order(self):
		query = sql.build_select('table', {'col1':'col1_data', 'col2':'col2_data', '__order_by':'id DESC'});
		expecting = "SELECT * FROM table WHERE col1 = 'col1_data' AND col2 = 'col2_data' ORDER BY id DESC"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_distinct(self):
		query = sql.build_select('table', {'col1':'col1_data', 'col2':'col2_data', '__select_keyword':'DISTINCT'});
		expecting = "SELECT DISTINCT * FROM table WHERE col1 = 'col1_data' AND col2 = 'col2_data'"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_in(self):
		query = sql.build_select('table', {'col1':['col1_data', 'col2_data']});
		expecting = "SELECT * FROM table WHERE col1 IN ('col1_data', 'col2_data')"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_not_in(self):
		query = sql.build_select('table', {'col1':sql.NOT(['col1_data', 'col2_data'])});
		expecting = "SELECT * FROM table WHERE col1 NOT IN ('col1_data', 'col2_data')"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_in_limit(self):
		query = sql.build_select('table', {'col1':['col1_data', 'col2_data'], '__limit':5});
		expecting = "SELECT * FROM table WHERE col1 IN ('col1_data', 'col2_data') LIMIT 5"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_none(self):
		query = sql.build_select('table', {'col1':None});
		expecting = "SELECT * FROM table WHERE col1 IS NULL"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))

	def test_build_select_raw(self):
		query = sql.build_select('table', {'col1':sql.RAW("%s = ENCRYPT('something', SUBSTRING(col1,1,2))")});
		expecting = "SELECT * FROM table WHERE col1 = ENCRYPT('something', SUBSTRING(col1,1,2))"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))

	def test_build_select_not(self):
		query = sql.build_select('table', {'col1':sql.NOT("somestring")});
		expecting = "SELECT * FROM table WHERE col1 <> 'somestring'"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))

	def test_build_select_gt(self):
		query = sql.build_select('table', {'col1':sql.GT("somestring")});
		expecting = "SELECT * FROM table WHERE col1 > 'somestring'"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))

	def test_build_select_lt(self):
		query = sql.build_select('table', {'col1':sql.LT("somestring")});
		expecting = "SELECT * FROM table WHERE col1 < 'somestring'"
		self.failUnlessEqual(query, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
