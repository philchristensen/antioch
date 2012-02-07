# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
antioch configuration helpers

This module implements support for defining different
environment types, such as development, testing, and
production. The appropriate configuration details are
loaded from a series of YAML files inside this module
directory, or optionally elsewhere in the filesystem.
"""

from __future__ import with_statement

import sys, os, os.path, yaml, warnings, threading
import pkg_resources as pkg

from django.conf import settings
from django.utils import importlib

configured = False
configured_lock = threading.BoundedSemaphore()

def get(key):
	translated_key = key.upper().replace('-', '_')
	return getattr(settings, translated_key)

def load_yaml(conf, package=None):
	"""
	Attempt to load the requested config file.

	If package=True, we look inside the conf module, otherwise
	it's assumed to be a filesystem path.
	"""
	try:
		if(package):
			f = pkg.resource_stream(package, conf)
		else:
			f = open(conf, 'r')
	except IOError, e:
		if(conf != 'development.yaml'):
			warnings.warn("Couldn't load %s conf: %s" % (conf, e))
		return {}
	# can't use with here, because pkg.resource_stream returns
	# a cStringIO object
	try:
		try:
			c = yaml.load(f)
		except Exception, e:
			raise SyntaxError('%s: %s' % (conf, e))
	finally:
		f.close()
	return c

def merge(content, into):
	"""
	Recursively dictionary `content` into `into`.

	No, dict.update() doesn't already do this ;-)
	"""
	for k, v in content.items():
		if k in into and isinstance(v, dict) and isinstance(into[k], dict):
			into[k] = merge(into[k], v)
		else:
			into[k] = v
	return into

def init(site_config='/etc/antioch.yaml', package='antioch.conf', filter=None, initLogging=True):
	"""
	Bootstrap the Django settings module.
	"""
	global configured
	if(configured):
		return
	
	result = dict()
	
	# with no config, it's a development environment
	env = 'development'
	
	# see if this server has a assigned environment
	site_environ_file = site_config.replace('.yaml', '.env')
	if(os.path.exists(site_environ_file)):
		with open(site_environ_file) as f:
			env = f.read().strip()
	
	# allow overriding at the command-line for debug/emergencies
	if('ENVIRONMENT' in os.environ):
		env = os.environ['ENVIRONMENT']
		warnings.warn("Overriding Django settings with os.environ['ENVIRONMENT'] ('%s')" % env)
	
	# load the default config file.
	default = load_yaml('default.yaml', package=package)
	# merge in the environment-specific config
	environ = merge(load_yaml('%s.yaml' % env, package=package), default)
	
	# if there's a site config file, merge that in as well
	# (NOTE: only secure params like database details and
	# external passwords are kept in the site config.)
	if(os.path.isfile(site_config)):
		environ = merge(load_yaml(site_config, package=None), environ)

	# the optional filter is a method that returns updates to the
	# final settings dict. this is used to override the database
	# config during unit testing.
	if(callable(filter)):
		warnings.warn("Overriding Django settings with %r" % filter)
		environ = merge(filter(environ), environ)
	
	settings.configure(ENVIRONMENT=env, **environ)
	# some debug pages use this variable (improperly, imho)
	settings.SETTINGS_MODULE = os.environ['DJANGO_SETTINGS_MODULE'] = 'antioch.settings'
	
	# Settings are configured, so we can set up the logger if required
	if initLogging and settings.LOGGING_CONFIG:
		# First find the logging configuration function ...
		logging_config_path, logging_config_func_name = settings.LOGGING_CONFIG.rsplit('.', 1)
		logging_config_module = importlib.import_module(logging_config_path)
		logging_config_func = getattr(logging_config_module, logging_config_func_name)
		
		# ... then invoke it with the logging settings
		logging_config_func(settings.LOGGING)
	
	try:
		configured_lock.acquire()
		configured = True
	finally:
		configured_lock.release()

