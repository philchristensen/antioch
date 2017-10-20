# antioch
# Copyright (c) 1999-2017 Phil Christensen
#
# See LICENSE for details

"""
Provide testing for the codebase
"""

import pkg_resources as pkg

from antioch.core import bootstrap
from django.conf import settings

# psql_path = settings.PSQL_PATH

pool = {}

def init_database(dbid, dataset='minimal', autocommit=False):
    global pool
    if(dbid not in pool and len(pool) == 1):
        key, p = pool.items()[0]
        p.close()
        del pool[key]
    elif(dbid in pool):
        return pool[dbid]
    
    db_url = settings.DB_URL_TEST
    
    bootstrap.initialize_database(psql_path, db_url)
    
    schema_path = pkg.resource_filename('antioch.core.bootstrap', 'schema.sql')
    bootstrap.load_schema(psql_path, db_url, schema_path)
    
    pool[dbid] = dbapi.connect(db_url, **dict(
        autocommit        = autocommit,
    ))
    bootstrap_path = pkg.resource_filename('antioch.core.bootstrap', '%s.py' % dataset)
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