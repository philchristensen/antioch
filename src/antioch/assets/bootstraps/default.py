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

def getsource(fn):
	from antioch import assets
	with open(assets.get('bootstraps/default-verbs', fn), 'r') as f:
		return f.read()

for name in model.default_permissions:
	exchange.pool.runOperation(sql.build_insert('permission', name=name))

exchange.load_permissions()

system = exchange.instantiate('object', name='System Object')
set_default_permissions_verb = model.Verb(system)
set_default_permissions_verb._method = True
set_default_permissions_verb._code = getsource('system_set_default_permissions.py')
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

edit_verb = exchange.instantiate('verb', dict(
	owner_id = wizard.get_id(),
	origin_id = wizard_class.get_id(),
	ability = True,
	method = False,
	code = getsource('wizard_class_edit.py'),
))
edit_verb.add_name('@edit')

exec_verb = exchange.instantiate('verb', dict(
	owner_id = wizard.get_id(),
	origin_id = wizard_class.get_id(),
	ability = True,
	method = False,
	code = getsource('wizard_class_exec.py'),
))
exec_verb.add_name('@exec')
exec_verb.allow('wizards', 'execute')

eval_verb = exchange.instantiate('verb', dict(
	owner_id = wizard.get_id(),
	origin_id = wizard_class.get_id(),
	ability = True,
	method = False,
	code = getsource('wizard_class_eval.py'),
))
eval_verb.add_name('@eval')
eval_verb.allow('wizards', 'execute')

set_verb = exchange.instantiate('verb', dict(
	owner_id = wizard.get_id(),
	origin_id = player_class.get_id(),
	ability = True,
	method = False,
	code = getsource('player_class_set.py'),
))
set_verb.add_name('@set')
set_verb.allow('everyone', 'execute')

alias_verb = exchange.instantiate('verb', dict(
	origin_id = author_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = getsource('author_class_alias.py'),
))
alias_verb.add_name('@alias')
alias_verb.allow('everyone', 'execute')

dig_verb = exchange.instantiate('verb', dict(
	origin_id = author_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = getsource('author_class_dig.py'),
))
dig_verb.add_name('@dig')
dig_verb.allow('everyone', 'execute')

tunnel_verb = exchange.instantiate('verb', dict(
	origin_id = author_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = getsource('author_class_tunnel.py'),
))
tunnel_verb.add_name('@tunnel')
tunnel_verb.allow('everyone', 'execute')

describe_verb = exchange.instantiate('verb', dict(
	origin_id = author_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = getsource('author_class_describe.py'),
))
describe_verb.add_name('@describe')
describe_verb.allow('everyone', 'execute')

look_verb = exchange.instantiate('verb', dict(
	origin_id = player_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = True,
	code = getsource('player_class_look.py'),
))
look_verb.add_name('look')
look_verb.allow('everyone', 'execute')

go_verb = exchange.instantiate('verb', dict(
	origin_id = player_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = getsource('player_class_go.py'),
))
go_verb.add_name('go')
go_verb.allow('everyone', 'execute')

say_verb = exchange.instantiate('verb', dict(
	origin_id = player_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = getsource('player_class_say.py'),
))
say_verb.add_name('say')
say_verb.allow('everyone', 'execute')

passwd_verb = exchange.instantiate('verb', dict(
	origin_id = player_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = True,
	code = getsource('player_class_passwd.py'),
))

passwd_verb.add_name('@passwd')
passwd_verb.allow('everyone', 'execute')