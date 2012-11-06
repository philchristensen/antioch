# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Create a fresh database
"""

from __future__ import with_statement

import pkg_resources as pkg

import traceback, subprocess

from antioch import plugins
from antioch.core import dbapi, exchange, parser

def initialize_database(psql_path, db_url, psql_args=[], quiet=True):
	"""
	Initialize a new database and user specified by the provided db_url.

	@param psql_path: the path to the `psql` binary
	@type psql_path: str

	@param db_url: the database connection string
	@type db_url: str

	@param psql_args: additional args to pass to `psql`
	@type psql_args: [str]

	@param quiet: if True, suppress stdout and stderr messages
	@type quiet: bool (default: True)
	"""
	dsn = parser.URL(db_url)

	kwargs = {}
	if(quiet):
		kwargs['stderr'] = subprocess.STDOUT

	subprocess.Popen([psql_path,
		'-h', dsn.get('host') or 'localhost',
		'-p', dsn.get('port') or '5432',
		'-U', 'postgres',
		'-c', "CREATE USER %(user)s WITH UNENCRYPTED PASSWORD '%(passwd)s';" % dsn,
	] + list(psql_args), stdout=subprocess.PIPE, **kwargs).wait()

	subprocess.Popen([psql_path,
		'-h', dsn.get('host') or 'localhost',
		'-p', dsn.get('port') or '5432',
		'-U', 'postgres',
		'-c', 'DROP DATABASE %s;' % dsn['path'][1:],
	] + list(psql_args), stdout=subprocess.PIPE, **kwargs).wait()

	subprocess.Popen([psql_path,
		'-h', dsn.get('host') or 'localhost',
		'-p', dsn.get('port') or '5432',
		'-U', 'postgres',
		'-c', 'CREATE DATABASE %s WITH OWNER %s;' % (dsn['path'][1:], dsn['user']),
	] + list(psql_args), stdout=subprocess.PIPE, **kwargs).wait()

def load_schema(psql_path, db_url, schema_path):
	"""
	Load a provided schema into the specified database.

	@param psql_path: the path to the `psql` binary
	@type psql_path: str

	@param db_url: the database connection string
	@type db_url: str

	@param schema_path: path to the database schema to load
	@type schema_path: str
	"""
	dsn = parser.URL(db_url)

	cmd = [psql_path,
		'-f', schema_path,
		'-h', dsn['host'],
		'-p', dsn.get('port') or '5432',
		'-U', dsn['user'],
		dsn['path'][1:],
	]

	child = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
	child.wait()

def load_python(pool, python_path):
	"""
	Execute a provided Python bootstrap file against the provided database.

	@param pool: the current database connection
	@type pool: L{antioch.dbapi.SynchronousConnectionPool}
	"""
	with exchange.ObjectExchange(pool) as x:
		execfile(python_path, globals(), dict(exchange=x))

def initialize_plugins(pool):
	for plugin in plugins.iterate():
		with exchange.ObjectExchange(pool) as x:
			if not(callable(getattr(plugin, 'initialize', None))): 
				continue
			plugin.initialize(x)

def get_verb_path(filename, dataset='default'):
	return pkg.resource_filename('antioch.core.bootstrap', '%s_verbs/%s' % (dataset, filename))

def get_source(filename, dataset='default'):
	verb_path = pkg.resource_filename('antioch.core.bootstrap', '%s_verbs/%s' % (dataset, filename))
	with open(verb_path) as f:
		return f.read()

