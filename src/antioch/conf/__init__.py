# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
JSON configuration file support.
"""

import os.path
import pkg_resources as pkg

import simplejson

DEFAULT_CONF_PATH = '/etc/antioch.json'

config = None

def load(path=DEFAULT_CONF_PATH):
	global config
	if(config):
		return config
	config = read_config(path)
	return config

def get(key):
	c = load()
	return c[key]

def read_config(path):
	if(os.path.exists(path)):
		f = open(path)
	else:
		path = 'Default config'
		f = pkg.resource_stream('antioch.conf', 'antioch.json')
	
	with f:
		try:
			c = simplejson.load(f)
		except Exception, e:
			raise SyntaxError('%s: %s' % (path, e))
		if(not isinstance(c, dict)):
			raise SyntaxError("%s doesn't contain a single top-level object." % path)
		return c
