#!/usr/bin/env python

# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Initialize a new txspace universe.
"""

import os.path, sys
sys.path.append('.')

from twisted.python import usage

from txspace import bootstrap, transact, dbapi, assets

default_bootstrap_path = 'bootstraps/%s.py'
default_schema_path = 'bootstraps/schema.sql'

class Options(usage.Options):
	"""
	Implement usage parsing for the mkspace script.
	"""
	optParameters = [
					["with-psql", "k", "psql", "Path to the psql binary"],
					["schema-file", "z", None, "The database schema file to use."],
					["bootstrap-file", "b", None, "The database bootstrap file to use."],
					]
	
	synopsis = "Usage: mkspace.py [options] <db-url|'default'> <dataset-name> [<psql-arg>*]"
	
	def parseArgs(self, db_url='default', dataset_name='default', *psql_args):
		if(db_url == 'default'):
			self['db-url'] = transact.default_db_url
		else:
			self['db-url'] = db_url
		self['dataset-name'] = dataset_name
		self['psql-args'] = psql_args

if(__name__ == '__main__'):
	config = Options()
	try:
		config.parseOptions()
	except usage.UsageError, e:
		print config.getSynopsis()
		print config.getUsage()
		print e.args[0]
		sys.exit(1)
	
	if(config['schema-file']):
		schema_path = config['schema-file']
	else:
		schema_path = assets.get(default_schema_path)
	schema_path = os.path.abspath(schema_path)
	
	if(config['bootstrap-file']):
		bootstrap_path = config['bootstrap-file']
	else:
		bootstrap_path = assets.get(default_bootstrap_path % config['dataset-name'])
	bootstrap_path = os.path.abspath(bootstrap_path)
	
	bootstrap.initialize_database(config['with-psql'], config['db-url'], quiet=False)
	bootstrap.load_schema(config['with-psql'], config['db-url'], schema_path, config['psql-args'])
	
	pool = dbapi.connect(config['db-url'])
	bootstrap.load_python(pool, bootstrap_path)
	