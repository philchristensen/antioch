# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Default database bootstrap.
"""

from __future__ import with_statement

from antioch import model, sql

def get_verb_path(filename):
	from antioch import assets
	return assets.get('bootstraps/default-verbs', filename)

def get_source(filename):
	from antioch import assets
	verb_path = assets.get('bootstraps/default-verbs', filename)
	with open(verb_path) as f:
		return f.read()

for name in model.default_permissions:
	exchange.pool.runOperation(sql.build_insert('permission', name=name))

exchange.load_permissions()

system = exchange.instantiate('object', name='System Object')
set_default_permissions_verb = model.Verb(system)
set_default_permissions_verb._method = True
set_default_permissions_verb._code = get_source('system_set_default_permissions.py')
exchange.save(set_default_permissions_verb)
set_default_permissions_verb.add_name('set_default_permissions')

wizard = exchange.instantiate('object', name='Wizard', unique_name=True)
wizard.set_owner(wizard)

system.set_owner(wizard)
set_default_permissions_verb.set_owner(wizard)
set_default_permissions_verb.allow('everyone', 'execute')
set_default_permissions_verb.allow('wizards', 'anything')

bag_of_holding = exchange.instantiate('object', name='bag of holding')
bag_of_holding.set_owner(wizard)
bag_of_holding.set_name('bag')

player_class = exchange.instantiate('object', name='player class')
player_class.set_location(bag_of_holding)
player_class.set_owner(wizard)

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
room_class.set_location(bag_of_holding)

room = exchange.instantiate('object', name='The Laboratory')
room.set_owner(wizard)
room.add_parent(room_class)
room.add_property('description', **dict(
	owner_id = wizard.get_id(),
	value = """A cavernous room filled with gadgetry of every kind,
this seems like a dumping ground for every piece of dusty forgotten
equipment a mad scientist might require.
""",
))

bag_of_holding.set_location(room)

phil = exchange.instantiate('object', name= 'Phil', unique_name=True)
phil.set_owner(phil)
phil.add_parent(player_class)

box = exchange.instantiate('object', name='box')
box.set_owner(phil)

wizard.set_location(room)
phil.set_location(room)
box.set_location(room)

wizard.set_player(True, is_wizard=True, passwd='wizard')
phil.set_player(True, passwd='phil')

wizard_class.add_verb('@reload', **dict(
	ability		= True,
	method		= False,
	code		= 'reload_filesystem_verbs()\nprint "Filesystem-based verbs will be reloaded from disk."',
))

wizard_class.add_verb('@edit', **dict(
	ability		= True,
	method		= False,
	filename	= get_verb_path('wizard_class_edit.py')
))

wizard_class.add_verb('@exec', **dict(
	ability		= True,
	method		= False,
	filename	= get_verb_path('wizard_class_exec.py')
)).allow('wizards', 'execute')

wizard_class.add_verb('@eval', **dict(
	ability		= True,
	method		= False,
	filename	= get_verb_path('wizard_class_eval.py')
)).allow('wizards', 'execute')

author_class.add_verb('@alias', **dict(
	ability		= True,
	method		= False,
	filename	= get_verb_path('author_class_alias.py')
)).allow('everyone', 'execute')

author_class.add_verb('@dig', **dict(
	ability		= True,
	method		= False,
	filename	= get_verb_path('author_class_dig.py')
)).allow('everyone', 'execute')

author_class.add_verb('@tunnel', **dict(
	ability		= True,
	method		= False,
	filename	= get_verb_path('author_class_tunnel.py')
)).allow('everyone', 'execute')

author_class.add_verb('@describe', **dict(
	ability		= True,
	method		= False,
	filename	= get_verb_path('author_class_describe.py')
)).allow('everyone', 'execute')

player_class.add_verb('@set', **dict(
	ability		= True,
	method		= False,
	filename	= get_verb_path('player_class_set.py')
)).allow('everyone', 'execute')

player_class.add_verb('look', **dict(
	ability		= True,
	method		= True,
	filename	= get_verb_path('player_class_look.py')
)).allow('everyone', 'execute')

player_class.add_verb('go', **dict(
	ability		= True,
	method		= False,
	filename	= get_verb_path('player_class_go.py')
)).allow('everyone', 'execute')

player_class.add_verb('say', **dict(
	ability		= True,
	method		= False,
	filename	= get_verb_path('player_class_say.py')
)).allow('everyone', 'execute')

player_class.add_verb('@passwd', **dict(
	ability		= True,
	method		= False,
	filename	= get_verb_path('player_class_passwd.py')
)).allow('everyone', 'execute')
