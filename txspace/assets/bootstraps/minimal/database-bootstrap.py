# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Default database bootstrap.
"""

from txspace import model, sql

for name in model.default_permissions:
	exchange.pool.runOperation(sql.build_insert('permission', name=name))

system = exchange.instantiate('object', name='System Object')
set_default_permissions_verb = model.Verb(system)
set_default_permissions_verb._method = True
set_default_permissions_verb._code = """#!txspace
obj = args[0]
obj.allow('wizards', 'anything')
obj.allow('owners', 'anything')
obj.allow('everyone', 'read')
"""
exchange.save(set_default_permissions_verb)
set_default_permissions_verb.add_name('set_default_permissions')

wizard = exchange.instantiate('object', name='Wizard', unique_name=True)
wizard.set_owner(wizard)

system.set_owner(wizard)
set_default_permissions_verb.set_owner(wizard)

room = exchange.instantiate('object', name='The Laboratory')
room.set_owner(wizard)

phil = exchange.instantiate('object', name= 'Phil', unique_name=True)
phil.set_owner(phil)

box = exchange.instantiate('object', name='box')
box.set_owner(phil)

wizard.set_location(room)
phil.set_location(room)
box.set_location(room)

wizard.set_player(True, is_wizard=True, passwd='wizard')
phil.set_player(True, passwd='phil')

exec_verb = exchange.instantiate('verb', dict(
	owner_id = wizard.get_id(),
	origin_id = wizard.get_id(),
	ability = True,
	method = False,
	code = """#!txspace
exec(command[6:])
""",
))
exec_verb.add_name('@exec')

eval_verb = exchange.instantiate('verb', dict(
	owner_id = wizard.get_id(),
	origin_id = wizard.get_id(),
	ability = True,
	method = False,
	code = """#!txspace
write(caller, eval(command[6:]))
""",
))
eval_verb.add_name('@eval')

look_verb = exchange.instantiate('verb', dict(
	origin_id = wizard.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = """#!txspace
if(dobj_str):
	obj = get_dobj()
else:
	obj = caller.get_location()

observations = dict(
	id				= obj.get_id(),
	name			= obj.get_name(),
	location_id		= obj._location_id or 0,
	description		= obj.get('description', 'Nothing much to see here.').value,
	contents		= [
		dict(
			type	= item.is_player(),
			name	= item.get_name(),
			image	= item.get('image', None).value,
			mood	= item.get('mood', None).value,
		) for item in obj.get_contents() if item.get('visible', True).value
	],
)

observe(caller, observations)
""",
))
look_verb.add_name('look')