# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import os.path

import pkg_resources as pkg

from nevow import loaders, rend

from antioch import assets

class EditorDelegatePage(rend.Page):
	def __init__(self, user):
		self.user = user
		
		assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'webroot'))
		assets.enable_assets(self, assets_path)
	
	def locateChild(self, ctx, segments):
		if(segments and self.user and segments[0] in ('object', 'verb', 'property', 'access')):
			template = pkg.resource_string('antioch.modules.editors', 'templates/%s-editor.xml' % segments[0])
			className = segments[0].capitalize() + 'Editor'
			cls = type(className, (rend.Page,), dict(
				docFactory		= loaders.xmlstr(template),
				user			= self.user,
				render_jquery	= lambda s,c,d: assets.render_jquery_tags(),
			))
			return (cls(), segments[2:])
		
		return super(rend.Page, self).locateChild(ctx, segments)

