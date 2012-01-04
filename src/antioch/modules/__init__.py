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
from django.conf.urls.defaults import include
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

def autodiscover():
	"""
	Auto-discover INSTALLED_APPS plugin.py modules and fail silently when
	not present.
	"""
	from django.conf import settings
	from django.utils.importlib import import_module
	from django.utils.module_loading import module_has_submodule
	
	from antioch import module
	
	for app in settings.INSTALLED_APPS:
		mod = import_module(app)
		# Attempt to import the app's plugin module.
		try:
			plugin_mod = import_module('%s.plugin' % app)
			for mod_name in dir(plugin_mod):
				if(mod_name.startswith('_')):
					continue
				p = getattr(plugin_mod, mod_name)
				if(module.IModule.providedBy(p)):
					yield p
		except:
			# Decide whether to bubble up this error. If the app just
			# doesn't have a plugin module, we can ignore the error
			# attempting to import it, otherwise we want it to bubble up.
			if module_has_submodule(mod, 'plugin'):
				raise

def iterate():
	for module in autodiscover():
		yield module()

def get(name):
	for plugin_mod in autodiscover():
		if(module.name == name):
			m = module()
			return m
	return None

def discover_commands(mod):
	from antioch.core import transact
	t = mod.__dict__.items()
	return dict(
		[(k,v) for k,v in t if isinstance(v, type) and issubclass(v, transact.WorldTransaction)]
	)

def discover_urlconfs():
	result = []
	for app in settings.INSTALLED_APPS:
		# Attempt to import the app's plugin module.
		mod = import_module(app)
		if(module_has_submodule(mod, 'plugin')):
			try:
				result.append(include('%s.urls' % app))
			except:
				if(module_has_submodule(mod, 'urls')):
					raise
	return result
