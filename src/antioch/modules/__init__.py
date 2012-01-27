# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Modules add additional client or server functionality
"""

import os, sys

from zope import interface

from twisted import plugin

from django.conf import settings
from django.conf.urls.defaults import include, url
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

module_cache = {}

def iterate():
	"""
	Auto-discover INSTALLED_APPS plugin.py modules and fail silently when
	not present.
	"""
	for app in settings.INSTALLED_APPS:
		plugin_mod = get_app_submodule(app, submodule='plugin')
		if(plugin_mod):
			yield instantiate(plugin_mod)

def discover_commands(mod):
	from antioch.core import transact
	t = mod.__dict__.items()
	return dict(
		[(k,v) for k,v in t if isinstance(v, type) and issubclass(v, transact.WorldTransaction)]
	)

def discover_urlconfs():
	result = []
	for app in settings.INSTALLED_APPS:
		p = get_app_submodule(app, submodule='plugin')
		if(p and get_app_submodule(app, submodule='urls')):
			p = instantiate(p)
			urlconf = url(r'^%s/' % p.name, include('%s.urls' % app))
			result.append(urlconf)
	return result

def get_app_submodule(app, submodule):
	mod = import_module(app)
	# Attempt to import the app's plugin module.
	try:
		return import_module('%s.%s' % (app, submodule))
	except:
		# Decide whether to bubble up this error. If the app just
		# doesn't have a plugin module, we can ignore the error
		# attempting to import it, otherwise we want it to bubble up.
		if module_has_submodule(mod, submodule):
			raise

# def iterate():
# 	for module in autodiscover():
# 		yield instantiate(module)

def get(name):
	for plugin_mod in iterate():
		m = instantiate(module)
		if(m.name == name):
			return m
	return None

def instantiate(mod):
	from antioch import module
	global module_cache
	if(mod not in module_cache):
		for name in dir(mod):
			if(name.startswith('_')):
				continue
			p = getattr(mod, name)
			if(module.IModule.providedBy(p)):
				module_cache[mod] = p()
	if(mod not in module_cache):
		raise RuntimeError("Could not instantiate an antioch module from %r" % mod)
	return module_cache[mod]

