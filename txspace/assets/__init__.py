# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import os.path

from nevow import static

def enable_assets(rsrc):
	assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'webroot'))
	assets_root = static.File(assets_path)
	rsrc.putChild('assets', assets_root)

def get_template_path(template_name):
	module_dir = os.path.dirname(__file__)
	template_path = os.path.join(module_dir, 'templates', template_name + '.xml')
	absolute_path = os.path.abspath(template_path)
	return absolute_path

def get_verbdir():
	return get('verbs')

def get(*path):
	item_path = os.path.join(os.path.dirname(__file__), *path)
	absolute_path = os.path.abspath(item_path)
	return absolute_path
	