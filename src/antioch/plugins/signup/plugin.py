# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Online signup for new players.
"""

from zope.interface import classProvides

from antioch import IPlugin

class SignupModule(object):
	classProvides(IPlugin)
	
	script_url = None
	
	def get_environment(self):
		return dict()

