# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Bootstrap support code.
"""

from __future__ import with_statement

import traceback, subprocess

from txspace import exchange, dbapi

def get_dsn(db_url):
	match = dbapi.URL_RE.match(db_url)
	if not(match):
		raise ValueError("Invalid db URL: %s" % db_url)
	dsn = match.groupdict()
	dsn['db'] = dsn['db'][1:]
	return dsn

def initialize_database(psql_path, db_url):
	dsn = get_dsn(db_url)
	
	subprocess.Popen([psql_path,
		'-h', dsn.get('host') or 'localhost',
		'-p', dsn.get('port') or '5432',
		'-U', 'postgres',
		'-c', "CREATE USER %(user)s WITH UNENCRYPTED PASSWORD '%(passwd)s';" % dsn,
	], stdout=subprocess.PIPE).wait()
	
	subprocess.Popen([psql_path,
		'-h', dsn.get('host') or 'localhost',
		'-p', dsn.get('port') or '5432',
		'-U', 'postgres',
		'-c', 'CREATE DATABASE %(db)s WITH OWNER %(user)s;' % dsn,
	], stdout=subprocess.PIPE).wait()

def drop_database(psql_path, db_url):
	dsn = get_dsn(db_url)
	
	subprocess.Popen([psql_path,
		'-h', dsn.get('host') or 'localhost',
		'-p', dsn.get('port') or '5432',
		'-U', 'postgres',
		'-c', 'DROP DATABASE %(db)s;' % dsn,
	], stdout=subprocess.PIPE).wait()

def load_schema(psql_path, db_url, schema_path, psql_args=[], create=False):
	dsn = get_dsn(db_url)
	
	cmd = [psql_path,
		'-f', schema_path,
		'-h', dsn.get('host') or 'localhost',
		'-p', dsn.get('port') or '5432',
		'-U', dsn.get('user') or 'postgres',
		dsn.get('db') or 'txspace',
	] + list(psql_args)
	
	child = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
	child.wait()

def load_python(pool, python_path):
	x = exchange.ObjectExchange(pool)
	execfile(python_path, globals(), dict(exchange=x))
