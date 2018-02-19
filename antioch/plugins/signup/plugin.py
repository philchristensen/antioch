# antioch
# Copyright (c) 1999-2017 Phil Christensen
#
#
# See LICENSE for details

"""
Online signup for new players.
"""

import logging

import pkg_resources as pkg

from zope.interface import classProvides

from antioch import IPlugin
from antioch.util import ason
from antioch.core import parser, code

log = logging.getLogger(__name__)

class SignupPlugin(object):
    classProvides(IPlugin)
    
    script_url = None
    
    def initialize(self, exchange):
        p = 'antioch.plugins.signup.verbs'
        system = exchange.get_object(1)
        system.add_verb('add_player', **dict(
            method        = True,
            filename    = pkg.resource_filename(p, 'system_add_player.py')
        ))
        
        system.add_verb('enable_player', **dict(
            method        = True,
            filename    = pkg.resource_filename(p, 'system_enable_player.py')
        ))
    
    def get_environment(self):
        def add_player(p, name=None, passwd=None, enabled=True):
            system = p.exchange.get_object(1)
            p.caller and p.caller.is_allowed('administer', system, fatal=True)
            klass = p.exchange.get_object('player class')
            user = p.exchange.instantiate('object', name=name, unique_name=True)
            user.set_owner(user)
            user.set_player(is_player=False, passwd=passwd)
            return user
    
        def enable_player(p, user):
            user.set_player(is_player=True)
            
        return dict(
            add_player        = add_player,
            enable_player    = enable_player,
        )

