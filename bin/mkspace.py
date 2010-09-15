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

default_bootstrap_path = assets.get('bootstraps/%s.py')
default_schema_path = assets.get('bootstraps/schema.sql')

class Options(usage.Options):
	"""
	Implement usage parsing for the mkspace script.
	"""
	optParameters = [
					["with-psql", "k", "psql", "Path to the psql binary"],
					["schema-file", "z", default_schema_path, "The database schema file to use."],
					["bootstrap-file", "b", default_bootstrap_path, "The database bootstrap file to use."],
					]
	
	synopsis = "Usage: mkspace.py [options] <db-url|'default'> <dataset-name> [<psql-arg>*]"
	
	def parseArgs(self, db_url, dataset_name, *psql_args):
		if(db_url == 'default'):
			self['db-url'] = transact.db_url
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
	
	schema_path = os.path.abspath(config['schema-file'])
	bootstrap_path = os.path.abspath(config['bootstrap-file'] % config['dataset-name'])
	
	bootstrap.initialize_database(config['with-psql'], config['db-url'])
	bootstrap.load_schema(config['with-psql'], config['db-url'], schema_path, config['psql-args'])
	
	pool = dbapi.connect(config['db-url'])
	bootstrap.load_python(pool, bootstrap_path)
	