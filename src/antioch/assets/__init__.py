# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import os.path

import pkg_resources as pkg

from twisted.python import filepath

from nevow import static, dirlist

def enable_assets(rsrc, assets_path=None, name='assets'):
	"""
	Activate a static.File resource as a child of the given Resource.
	"""
	if(assets_path is None):
		assets_path = pkg.resource_filename(__name__, 'webroot')
	assets_root = static.File(assets_path)
	rsrc.putChild(name, assets_root)

def get(*path):
	"""
	Get a path relative to the assets package.
	"""
	item_path = os.path.join(os.path.dirname(__file__), *path)
	absolute_path = os.path.abspath(item_path)
	return absolute_path

