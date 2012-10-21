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

class RegistrationModule(object):
	classProvides(IPlugin)
	
	name = u'registration'
	
	def get_environment(self):
		return dict()

