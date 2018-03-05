# antioch
# Copyright (c) 1999-2018 Phil Christensen
#
# See LICENSE for details

"""
Provide testing for the codebase
"""

import pkg_resources as pkg

from antioch.core import bootstrap
from django.conf import settings
from django.db import connection

def init_database(dbid, dataset='minimal', autocommit=False):
    bootstrap_path = pkg.resource_filename('antioch.core.bootstrap', '%s.py' % dataset)
    
    bootstrap.load_python(connection, bootstrap_path)
    bootstrap.initialize_plugins(connection)

    return connection

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