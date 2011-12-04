# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

import os.path

from nevow import rend

class AskDelegatePage(rend.Page):
	def __init__(self):
		assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'webroot'))
		assets.enable_assets(self, assets_path)
	
