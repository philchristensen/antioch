# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import os.path

from nevow import static

def enable_assets(rsrc, assets_path=None, name='assets'):
	if(assets_path is None):
		assets_path = os.path.join(os.path.dirname(__file__), 'webroot')
	assests_path = os.path.abspath(assets_path)
	assets_root = static.File(assets_path)
	rsrc.putChild(name, assets_root)

def get_template_path(template_name, module_dir=None):
	if(module_dir is None):
		module_dir = os.path.dirname(__file__)
	template_path = os.path.join(module_dir, 'templates', template_name + '.xml')
	absolute_path = os.path.abspath(template_path)
	return absolute_path

def get(*path):
	item_path = os.path.join(os.path.dirname(__file__), *path)
	absolute_path = os.path.abspath(item_path)
	return absolute_path
	