# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

from antioch import bootstrap, dbapi, assets, transact

psql_path = 'psql'

initialized = {}
pool = {}

#dbapi.debug = True

def get_test_db_url(suffix=''):
	url = transact.default_db_url.split('/')
	url[-1] = 'antioch_test' + suffix
	return '/'.join(url)

def init_database(dbid, dataset='minimal', autocommit=False):
	global initialized, pool
	if(initialized.get(dbid)):
		return pool.get(dbid)
	initialized[dbid] = True
	
	db_url = get_test_db_url(dbid.__name__.lower())
	
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