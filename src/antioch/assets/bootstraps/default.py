# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Default database bootstrap.
"""

from antioch import model, sql

for name in model.default_permissions:
	exchange.pool.runOperation(sql.build_insert('permission', name=name))

exchange.load_permissions()

system = exchange.instantiate('object', name='System Object')
set_default_permissions_verb = model.Verb(system)
set_default_permissions_verb._method = True
set_default_permissions_verb._code = """#!antioch
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
set_default_permissions_verb.allow('everyone', 'execute')
set_default_permissions_verb.allow('wizards', 'anything')

bag_of_holding = exchange.instantiate('object', name='bag of holding')
bag_of_holding.set_name('bag')
bag_of_holding.set_owner(wizard)

player_class = exchange.instantiate('object', name='player class')
player_class.set_location(bag_of_holding)
player_class.set_owner(wizard)

author_class = exchange.instantiate('object', name='author class')
author_class.add_parent(player_class)
author_class.set_location(bag_of_holding)
author_class.set_owner(wizard)

programmer_class = exchange.instantiate('object', name='programmer class')
programmer_class.add_parent(author_class)
programmer_class.set_location(bag_of_holding)
programmer_class.set_owner(wizard)

wizard_class = exchange.instantiate('object', name='wizard class')
wizard_class.add_parent(programmer_class)
wizard_class.set_location(bag_of_holding)
wizard_class.set_owner(wizard)
wizard.add_parent(wizard_class)

room_class = exchange.instantiate('object', name='room class')
room_class.set_location(bag_of_holding)
room_class.set_owner(wizard)

room = exchange.instantiate('object', name='The Laboratory')
room.set_owner(wizard)
room.add_parent(room_class)
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
	code = """#!antioch
if not has_pobj_str('on'):
	if(has_dobj()):
		subject = get_dobj()
	else:
		subject = get_object(get_dobj_str())
else:
	if(has_pobj('on')):
		origin = get_pobj('on')
	else:
		origin = get_object(get_pobj_str('on'))
	
	subjects = get_dobj_str().split(' ', 1)
	if(len(subjects) == 2):
		stype, name = subjects
	else:
		stype = None
		name = subjects[0]
	
	if(stype == 'verb'):
		subject = origin.get_verb(name)
		if subject is None:
			raise NoSuchVerbError(name)
	elif(stype in ('property', 'prop', 'value', 'val')):
		subject = origin.get_property(name)
		if subject is None:
			raise NoSuchPropertyError(name, origin)
	else:
		subject = origin.get_verb(name) or origin.get_property(name)
		if subject is None:
			raise NoSuchPropertyError(name, origin)

edit(subject)
""",
))
edit_verb.add_name('@edit')

exec_verb = exchange.instantiate('verb', dict(
	owner_id = wizard.get_id(),
	origin_id = wizard_class.get_id(),
	ability = True,
	method = False,
	code = """#!antioch
exec(command[6:].strip())
""",
))
exec_verb.add_name('@exec')

eval_verb = exchange.instantiate('verb', dict(
	owner_id = wizard.get_id(),
	origin_id = wizard_class.get_id(),
	ability = True,
	method = False,
	code = """#!antioch
write(caller, eval(command[6:].strip()))
""",
))
eval_verb.add_name('@eval')

alias_verb = exchange.instantiate('verb', dict(
	origin_id = author_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = """#!antioch
def usage():
	write(caller, "Usage: @alias (add <alias>|remove <alias>|list) on <object>", error=True)

result = []
if(has_dobj_str()):
	ds = get_dobj_str()
	result = ds.split(' ', 1)
	if(len(result) != 2):
		usage()
		return
else:
	usage()
	return

sub, alias = result
if(sub == 'add'):
	obj = get_pobj('to')
	obj.add_alias(alias)
	write(caller, "Alias %r added to %s" % (alias, obj))
elif(sub == 'remove'):
	obj = get_pobj('from')
	obj.remove_alias(alias)
	write(caller, "Alias %r removed from %s" % (alias, obj))
elif(sub == 'list'):
	obj = here.find(alias)
	aliases = obj.get_aliases()
	write(caller, "%s has the following aliases: %r" % (obj, aliases))
""",
))
alias_verb.add_name('@alias')
alias_verb.allow('everyone', 'execute')

dig_verb = exchange.instantiate('verb', dict(
	origin_id = author_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = """#!antioch
room_class = get_object('room class')
direction = get_dobj_str()

room = create_object(get_pobj_str('to'))
room.add_parent(room_class)
room.set_location(None)

if(here.has_property('exits')):
	exits = here['exits'].value
	exits[direction] = room
	here['exits'].value = exits
else:
	here.add_property('exits').value = {direction : room}

write(caller, "You dug a new room %s in the %s" % (room, direction))
""",
))
dig_verb.add_name('@dig')
dig_verb.allow('everyone', 'execute')

tunnel_verb = exchange.instantiate('verb', dict(
	origin_id = author_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = """#!antioch
room_class = get_object('room class')
direction = get_dobj_str()

room = get_object(get_pobj_str('to'))

if(here.has_property('exits')):
	exits = here['exits'].value
	exits[direction] = room
	here['exits'].value = exits
else:
	here.add_property('exits').value = {direction : room}

write(caller, "You dug a tunnel %s to %s" % (direction, room))
""",
))
tunnel_verb.add_name('@tunnel')
tunnel_verb.allow('everyone', 'execute')

describe_verb = exchange.instantiate('verb', dict(
	origin_id = author_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = """#!antioch
if not(has_dobj_str()):
	caller.write('What do you want to describe?', error=True)
	return
if not(has_pobj_str('as')):
	caller.write('What do you want to describe that as?', error=True)
	return

subject = get_dobj()
if(subject.has_property('description')):
	description = subject.get_property('description')
else:
	description = subject.add_property('description')

description.value = get_pobj_str('as')
write(caller, 'Description set for %s' % subject)
""",
))
describe_verb.add_name('@describe')
describe_verb.allow('everyone', 'execute')

look_verb = exchange.instantiate('verb', dict(
	origin_id = player_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = True,
	code = """#!antioch
if(__name__ == 'method'):
	obj = args[0] if args else caller.location
elif(has_dobj_str()):
	obj = get_dobj()
else:
	obj = caller.get_location()

observations = dict(
	id				= obj.get_id(),
	name			= obj.get_name(),
	location_id		= str(obj.get_location()) or 0,
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
if(obj.is_connected_player()):
	write(obj, "%s looks at you" % obj.get_name())

observe(caller, observations)
""",
))
look_verb.add_name('look')
look_verb.allow('everyone', 'execute')

go_verb = exchange.instantiate('verb', dict(
	origin_id = player_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = False,
	code = """#!antioch
if not(has_dobj_str()):
	write(caller, "Where do you want to go?", error=True)
	return

if not(caller.location.has_property('exits')):
	write(caller, "You can't go that way.", error=True)
	return

exits = caller.location['exits'].value
direction = get_dobj_str()

if(direction not in exits):
	write(caller, "You can't go that way.")
	return

caller.set_location(exits[direction])
caller.look()
""",
))
go_verb.add_name('go')
go_verb.allow('everyone', 'execute')

passwd_verb = exchange.instantiate('verb', dict(
	origin_id = player_class.get_id(),
	owner_id = wizard.get_id(),
	ability = True,
	method = True,
	code = """#!antioch
if(__name__ == '__method__'):
	user = get_object(args[0])
	if(args[1] == 'validate'):
		#TODO validate passwd
		if(user.validate_password(args[2])):
			ask('Please enter the new password:', self, user.get_id(), 'change')
		else:
			write(caller, "The password is incorrect. Please enter your *current* password for " + str(user))
	else:
		user.set_player(passwd=args[2])
		write(caller, "Changed password for " + str(user))
	return

if(has_dobj_str()):
	user = get_dobj()
else:
	user = caller

if(user == caller):
	ask('Please enter your current password:', self, user.get_id(), 'validate')
else:
	ask('Please enter the new password:', self, user.get_id(), 'change')
""",
))

passwd_verb.add_name('@passwd')
passwd_verb.allow('everyone', 'execute')