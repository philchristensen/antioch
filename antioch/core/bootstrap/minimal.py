# antioch
# Copyright (c) 1999-2017 Phil Christensen
#
#
# See LICENSE for details

"""
Default database bootstrap.
"""

from __future__ import with_statement

from antioch.core import interface, bootstrap
from antioch.util import sql

for name in interface.default_permissions:
    exchange.connection.runOperation(sql.build_insert('permission', name=name))

exchange.load_permissions()

system = exchange.instantiate('object', name='System Object')
set_default_permissions_verb = interface.Verb(system)
set_default_permissions_verb._method = True
set_default_permissions_verb._code = bootstrap.get_source('system_set_default_permissions.py')
exchange.save(set_default_permissions_verb)
set_default_permissions_verb.add_name('set_default_permissions')

set_default_permissions_verb(set_default_permissions_verb)
set_default_permissions_verb(system)

wizard = exchange.instantiate('object', name='Wizard', unique_name=True)
wizard.set_owner(wizard)
system.set_owner(wizard)
set_default_permissions_verb.set_owner(wizard)

player_defaults = exchange.instantiate('object', name= 'player defaults')
player_defaults.set_owner(wizard)
wizard.add_parent(player_defaults)

room = exchange.instantiate('object', name='The First Room', unique_name=True)
room.set_owner(wizard)

user = exchange.instantiate('object', name= 'User', unique_name=True)
user.set_owner(user)
user.add_parent(player_defaults)

wizard.set_location(room)
user.set_location(room)

wizard.set_player(True, is_wizard=True, passwd='wizard')
user.set_player(True, passwd='user')

wizard.add_verb('@edit', **dict(
    ability        = True,
    filename    = bootstrap.get_verb_path('wizard_class_edit.py'),
))

wizard.add_verb('@exec', **dict(
    ability        = True,
    filename    = bootstrap.get_verb_path('wizard_class_exec.py'),
)).allow('wizards', 'execute')

wizard.add_verb('@eval', **dict(
    ability        = True,
    filename    = bootstrap.get_verb_path('wizard_class_eval.py'),
)).allow('wizards', 'execute')

player_defaults.add_verb('@set', **dict(
    ability        = True,
    filename    = bootstrap.get_verb_path('player_class_set.py'),
)).allow('everyone', 'execute')

player_defaults.add_verb('look', **dict(
    ability        = True,
    method        = True,
    filename    = bootstrap.get_verb_path('player_class_look.py'),
)).allow('everyone', 'execute')

player_defaults.add_verb('@passwd', **dict(
    ability        = True,
    method        = True,
    filename    = bootstrap.get_verb_path('player_class_passwd.py'),
)).allow('everyone', 'execute')
