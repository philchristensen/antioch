# antioch
# Copyright (c) 1999-2017 Phil Christensen
#
#
# See LICENSE for details

"""
A highly-customizable, scalable game server for creating virtual worlds.
"""

from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

from zope import interface

from twisted.python import versions

version = versions.Version('antioch', 2, 0, 0, 1)
__version__ = version.short()

class IPlugin(interface.Interface):
    name = interface.Attribute('Name of this module.')
    script_url = interface.Attribute('Plugin script URL.')
    
    def get_environment(self):
        """
        Return a dict of items to add to the verb environment.
        """
    
    def handle_message(self, msg):
        """
        Handle a message generated by the verb environment.
        """
