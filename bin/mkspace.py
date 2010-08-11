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

default_bootstrap_path = assets.get('bootstraps/test/database-bootstrap.py')
default_schema_path = assets.get('bootstraps/test/database-schema.sql')
default_grants_path = assets.get('bootstraps/test/database-grants.sql')

class Options(usage.Options):
	"""
	Implement usage parsing for the mkspace script.
	"""
	optParameters = [
					["with-psql", "k", "psql", "Path to the psql binary"],
					["schema-file", "z", default_schema_path, "The database schema file to use."],
					["grants-file", "Z", default_grants_path, "The database grants file to use."],
					["bootstrap-file", "b", default_bootstrap_path, "The database bootstrap file to use."],
					]
	
	synopsis = "Usage: mkspace.py [options] <db-url|'default'> [<psql-arg>*]"
	
	def parseArgs(self, db_url, *psql_args):
		if(db_url == 'default'):
			self['db-url'] = transact.db_url
		else:
			self['db-url'] = db_url
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
	
	bootstrap.initialize_database(config['with-psql'], config['db-url'])
	bootstrap.load_schema(config['with-psql'], config['db-url'], os.path.abspath(config['schema-file']), config['psql-args'])
	
	pool = dbapi.connect(config['db-url'])
	bootstrap.load_python(pool, os.path.abspath(config['bootstrap-file']))
	