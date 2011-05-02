# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

"""
Provide testing for the codebase
"""

from antioch import bootstrap, dbapi, assets, transact, conf

psql_path = conf.get('psql-path')

pool = {}

def init_database(dbid, dataset='minimal', autocommit=False):
	global pool
	if(dbid not in pool and len(pool) == 1):
		key, p = pool.items()[0]
		p.close()
		del pool[key]
	elif(dbid in pool):
		return pool[dbid]
	
	db_url = conf.get('db-url-test')
	
	bootstrap.initialize_database(psql_path, db_url)
	
	schema_path = assets.get('bootstraps/schema.sql')
	bootstrap.load_schema(psql_path, db_url, schema_path)
	
	pool[dbid] = dbapi.connect(db_url, autocommit=autocommit)
	bootstrap_path = assets.get('bootstraps/%s.py' % dataset)
	bootstrap.load_python(pool[dbid], bootstrap_path)

	return pool[dbid]

def raise_e(e):
	raise e

class Anything(object):
	def __init__(self, **attribs):
		self.__dict__['attribs'] = attribs
	
	def __getattr__(self, key):
		if(key not in self.attribs):
			raise AttributeError(key)
		return self.attribs[key]
	
	def __setattr__(self, key, value):
		self.attribs[key] = value