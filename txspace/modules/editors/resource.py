# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import os.path

from nevow import loaders, rend

from txspace import assets

class EditorDelegatePage(rend.Page):
	def __init__(self, user):
		self.user = user
		
		assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'webroot'))
		assets.enable_assets(self, assets_path)
	
	def locateChild(self, ctx, segments):
		if(segments and self.user and segments[0] in ('object', 'verb', 'property', 'access')):
			module_dir = os.path.dirname(__file__)
			template = assets.get_template_path(segments[0] + '-editor', module_dir)
			className = ''.join([x.capitalize() for x in os.path.basename(template).split('-')])
			cls = type(className, (rend.Page,), dict(
				docFactory	= loaders.xmlfile(template),
				user		= self.user
			))
			return (cls(), segments[2:])
		
		return super(rend.Page, self).locateChild(ctx, segments)

