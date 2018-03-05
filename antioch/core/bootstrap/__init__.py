# antioch
# Copyright (c) 1999-2018 Phil Christensen
#
#
# See LICENSE for details

"""
Create a fresh database
"""



import pkg_resources as pkg

import traceback, subprocess

from antioch import plugins
from antioch.core import exchange, parser

def load_python(connection, python_path):
    """
    Execute a provided Python bootstrap file against the provided database.
    """
    with exchange.ObjectExchange(connection) as x:
        exec(compile(open(python_path).read(), python_path, 'exec'), globals(), dict(exchange=x))

def initialize_plugins(connection):
    for plugin in plugins.iterate():
        with exchange.ObjectExchange(connection) as x:
            if not(callable(getattr(plugin, 'initialize', None))): 
                continue
            plugin.initialize(x)

def get_verb_path(filename, dataset='default'):
    return pkg.resource_filename('antioch.core.bootstrap', '%s_verbs/%s' % (dataset, filename))

def get_source(filename, dataset='default'):
    verb_path = pkg.resource_filename('antioch.core.bootstrap', '%s_verbs/%s' % (dataset, filename))
    with open(verb_path) as f:
        return f.read()

