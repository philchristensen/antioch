#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: player_go.py 184 2007-03-04 18:54:05Z phil $
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("Where do you want to go?")
	return
if not(here.has_property("exits")):
	caller.write("You can't go that way.")
	return

choice = get_dobj_str().lower()
exits = here.get_property("exits")
if(here.has_property("exit_aliases")):
	aliases = here.get_property("exit_aliases")
else:
	aliases = []

if not(choice in exits or choice in aliases):
	caller.write("You can't go that way.")
	return

if(choice in exits):
	new_room = exits[choice]
else:
	new_room = exits[aliases[choice]]

if(get_obj('class_door').has_child(new_room)):
	if not(new_room.call_verb('enter')):
		return
	else:
		new_room = new_room.get_property('target')

caller.set_location(new_room)
