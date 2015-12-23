# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

import os.path, sys

import pkg_resources as pkg

from twisted.python import usage

from django.conf import settings

from antioch.core import dbapi, bootstrap

default_bootstrap_path = '%s.py'
default_schema_path = 'schema.sql'

class Options(usage.Options):
	"""
	Implement usage parsing for the mkspace script.
	"""
	optParameters = [
					["with-psql", "k", "psql", "Path to the psql binary"],
					["schema-file", "z", None, "The database schema file to use."],
					["bootstrap-file", "b", None, "The database bootstrap file to use."],
					]
	optFlags = [
					["no-init", "n", "Database already exists, don't create it."],
				]

	synopsis = "Usage: mkspace.py [options] <db-url|'default'> <dataset-name> [<psql-arg>*]"

	def parseArgs(self, db_url='default', dataset_name='default', *psql_args):
		if(db_url == 'default'):
			self['db-url'] = settings.DB_URL
		else:
			self['db-url'] = db_url
		self['dataset-name'] = dataset_name
		self['psql-args'] = psql_args

def main():
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
		schema_path = pkg.resource_filename('antioch.core.bootstrap', default_schema_path)
	schema_path = os.path.abspath(schema_path)

	if(config['bootstrap-file']):
		bootstrap_path = config['bootstrap-file']
	else:
		bootstrap_path = pkg.resource_filename('antioch.core.bootstrap', default_bootstrap_path % config['dataset-name'])
	bootstrap_path = os.path.abspath(bootstrap_path)
	
	if not(config['no-init']):
		bootstrap.initialize_database(config['with-psql'], config['db-url'], config['psql-args'], quiet=False)
	
	from django.core.management import call_command
	call_command('syncdb', interactive=False)
	call_command('migrate', interactive=False)
	
	pool = dbapi.connect(config['db-url'])
	bootstrap.load_python(pool, bootstrap_path)
	bootstrap.initialize_plugins(pool)

if(__name__ == '__main__'):
	main()