# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

from txspace import bootstrap, dbapi, assets, transact

psql_path = 'psql'

initialized = {}
pool = {}

# dbapi.debug = True

def init_database(dbid, dataset='minimal'):
	global initialized, pool, oscar
	if(initialized.get(dbid)):
		return pool.get(dbid)
	initialized[dbid] = True
	
	db_url = transact.db_url.split('/')
	db_url[-1] = 'txspace_test'
	db_url = '/'.join(db_url)
	
	bootstrap.initialize_database(psql_path, db_url)
	
	schema_path = assets.get('bootstraps/%s/database-schema.sql' % dataset)
	bootstrap.load_schema(psql_path, db_url, schema_path)
	
	pool[dbid] = dbapi.connect(db_url)
	bootstrap_path = assets.get('bootstraps/%s/database-bootstrap.py' % dataset)
	bootstrap.load_python(pool[dbid], bootstrap_path)

	return pool[dbid]

class Anything(object):
	def __init__(self, **attribs):
		self.__dict__['attribs'] = attribs
	
	def __getattr__(self, key):
		if(key not in self.attribs):
			raise AttributeError(key)
		return self.attribs[key]
	
	def __setattr__(self, key, value):
		self.attribs[key] = value