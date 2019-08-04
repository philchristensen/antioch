# antioch
# Copyright (c) 1999-2019 Phil Christensen
#
#
# See LICENSE for details

"""
Default database bootstrap.
"""



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

bag_of_holding = exchange.instantiate('object', name='bag of holding')
bag_of_holding.set_owner(wizard)
bag_of_holding.set_location(wizard)

author_hammer = exchange.instantiate('object', name='author hammer', unique_name=True)
author_hammer.set_owner(wizard)
author_hammer.set_location(bag_of_holding)

wizard_hammer = exchange.instantiate('object', name='wizard hammer', unique_name=True)
wizard_hammer.set_owner(wizard)
wizard_hammer.set_location(bag_of_holding)

player_class = exchange.instantiate('object', name='player class')
player_class.set_location(bag_of_holding)
player_class.set_owner(wizard)

guest_class = exchange.instantiate('object', name='guest class')
guest_class.set_owner(wizard)
guest_class.add_parent(player_class)
guest_class.set_location(bag_of_holding)

author_class = exchange.instantiate('object', name='author class')
author_class.set_owner(wizard)
author_class.add_parent(player_class)
author_class.set_location(bag_of_holding)

programmer_class = exchange.instantiate('object', name='programmer class')
programmer_class.set_owner(wizard)
programmer_class.add_parent(author_class)
programmer_class.set_location(bag_of_holding)

wizard_class = exchange.instantiate('object', name='wizard class')
wizard_class.set_owner(wizard)
wizard_class.add_parent(programmer_class)
wizard_class.set_location(bag_of_holding)
wizard.add_parent(wizard_class)

room_class = exchange.instantiate('object', name='room class')
room_class.set_owner(wizard)

laboratory = exchange.instantiate('object', name='The Laboratory', unique_name=True)
laboratory.set_owner(wizard)
laboratory.add_parent(room_class)
laboratory.add_property('description', **dict(
    owner_id = wizard.get_id(),
    value = """A cavernous laboratory filled with gadgetry of every kind,
this seems like a dumping ground for every piece of dusty forgotten
equipment a mad scientist might require.
""",
))

lobby = exchange.instantiate('object', name='The Lobby', unique_name=True)
lobby.set_owner(wizard)
lobby.add_parent(room_class)
lobby.add_property('description', **dict(
    owner_id = wizard.get_id(),
    value = """A dusty old waiting area, every minute spent in this room
feels like an eternity.
""",
))

wizard.set_location(laboratory)

wizard.set_player(True, is_wizard=True, passwd='wizard')

system.add_verb('authenticate', **dict(
    method        = True,
    filename    = 'system_authenticate.py',
    repo        = 'default',
    ref         = 'master'
))

system.add_verb('connect', **dict(
    method        = True,
    filename    = 'system_connect.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

system.add_verb('login', **dict(
    method        = True,
    filename    = 'system_login.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

system.add_verb('logout', **dict(
    method        = True,
    filename    = 'system_logout.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

wizard_class.add_verb('edit', **dict(
    ability        = True,
    filename    = 'wizard_class_edit.py',
    repo        = 'default',
    ref         = 'master'
))

wizard_class.add_verb('exec', **dict(
    ability        = True,
    filename    = 'wizard_class_exec.py',
    repo        = 'default',
    ref         = 'master'
)).allow('wizards', 'execute')

wizard_class.add_verb('eval', **dict(
    ability        = True,
    filename    = 'wizard_class_eval.py',
    repo        = 'default',
    ref         = 'master'
)).allow('wizards', 'execute')

wizard_class.add_verb('adduser', **dict(
    ability        = True,
    filename    = 'wizard_class_adduser.py',
    repo        = 'default',
    ref         = 'master'
)).allow('wizards', 'execute')

wizard_class.add_verb('passwd', **dict(
    ability        = True,
    method        = True,
    filename    = 'wizard_class_passwd.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

author_class.add_verb('alias', **dict(
    ability        = True,
    filename    = 'author_class_alias.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

author_class.add_verb('make', **dict(
    ability        = True,
    filename    = 'author_class_make.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

author_class.add_verb('inspect', **dict(
    ability        = True,
    filename    = 'author_class_inspect.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

author_class.add_verb('dig', **dict(
    ability        = True,
    filename    = 'author_class_dig.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

author_class.add_verb('tunnel', **dict(
    ability        = True,
    filename    = 'author_class_tunnel.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

author_class.add_verb('describe', **dict(
    ability        = True,
    filename    = 'author_class_describe.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

guest_class.add_verb('passwd', **dict(
    ability        = True,
    code        = 'write(caller, "Guests cannot change their passwords.")',
)).allow('everyone', 'execute')

player_class.add_verb('set', **dict(
    ability        = True,
    filename    = 'player_class_set.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

player_class.add_verb('look', **dict(
    ability        = True,
    method        = True,
    filename    = 'player_class_look.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

player_class.add_verb('go', **dict(
    ability        = True,
    filename    = 'player_class_go.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

player_class.add_verb('say', **dict(
    ability        = True,
    filename    = 'player_class_say.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

player_class.add_verb('hear', **dict(
    method        = True,
    filename    = 'player_class_hear.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

player_class.add_verb('passwd', **dict(
    ability        = True,
    filename    = 'player_class_passwd.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

room_class.add_verb('hear', **dict(
    method        = True,
    filename    = 'room_class_hear.py',
    repo        = 'default',
    ref         = 'master'
)).allow('everyone', 'execute')

author = exchange.instantiate('object', name='Author', unique_name=True)
author.set_owner(author)
author.set_location(laboratory)
author.set_player(True, passwd='author')
author.add_parent(author_class)
