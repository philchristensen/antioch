# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Default database bootstrap.
"""

from txspace import model

system = exchange.instantiate('object', name='System Object')
wizard = exchange.instantiate('object', name='Wizard', unique_name=True)
phil = exchange.instantiate('object', name= 'Phil', unique_name=True)

room = exchange.instantiate('object', name='The Laboratory')
box = exchange.instantiate('object', name='box')

system.set_owner(wizard)
wizard.set_owner(wizard)
room.set_owner(wizard)

phil.set_owner(phil)
box.set_owner(phil)

wizard.set_location(room)
phil.set_location(room)
box.set_location(room)

wizard.set_player(True, 'wizard')
phil.set_player(True, 'phil')

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