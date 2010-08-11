# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("Where do you want to go?", is_error=True)
	return
if not(here.has_property("exits")):
	caller.write("You can't go that way.", is_error=True)
	return

choice = get_dobj_str().lower()
exits = here.get_property("exits")
if(here.has_property("exit_aliases")):
	aliases = here.get_property("exit_aliases")
else:
	aliases = []

if not(choice in exits or choice in aliases):
	caller.write("You can't go that way.", is_error=True)
	return

if(choice in exits):
	new_room = exits[choice]
else:
	new_room = exits[aliases[choice]]

if(get_obj('class_door').has_child(new_room)):
	door = new_room
	if(door.has_verb('enter') and not door.call_verb('enter')):
		caller.write('%s appears to be locked.' % door, is_error=True)
		return
	else:
		new_room = new_room.get_property('target')

caller.set_location(new_room)
