# antioch
# Copyright (c) 1999-2018 Phil Christensen
#
#
# See LICENSE for details

"""
Plugins add additional client or server functionality
"""

import os, sys

from django.conf import settings
from django.conf.urls import include, url
from importlib import import_module
from django.utils.module_loading import module_has_submodule

plugin_cache = {}

def iterate():
    """
    Iterate through installed Django apps that are antioch plugins.
    """
    for app in settings.INSTALLED_APPS:
        plugin_mod = get_app_submodule(app, submodule='plugin')
        if(plugin_mod):
            yield instantiate(plugin_mod)

def urlconfs():
    """
    Return all urlconfs provided by antioch plugins.
    """
    result = []
    for app in settings.INSTALLED_APPS:
        app_label = app.split('.')[-1]
        p = get_app_submodule(app, submodule='plugin')
        if(p and get_app_submodule(app, submodule='urls')):
            urlconf = url(r'', include('%s.urls' % app))
            result.append(urlconf)
    return result

def get_app_submodule(app_name, submodule):
    app = import_module(app_name)
    # Attempt to import the app's plugin module.
    try:
        return import_module('%s.%s' % (app_name, submodule))
    except:
        # Decide whether to bubble up this error. If the app just
        # doesn't have a plugin module, we can ignore the error
        # attempting to import it, otherwise we want it to bubble up.
        if module_has_submodule(app, submodule):
            raise

def instantiate(plugin_mod):
    from antioch import IPlugin
    global plugin_cache
    if(plugin_mod not in plugin_cache):
        for name in dir(plugin_mod):
            if(name.startswith('_')):
                continue
            p = getattr(plugin_mod, name)
            if(IPlugin.providedBy(p)):
                plugin_cache[plugin_mod] = p()
    if(plugin_mod not in plugin_cache):
        raise RuntimeError("Could not instantiate an antioch plugin from %r" % plugin)
    return plugin_cache[plugin_mod]

