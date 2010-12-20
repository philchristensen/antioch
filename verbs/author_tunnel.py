#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: author_tunnel.py 184 2007-03-04 18:54:05Z phil $
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("In what direction do you want to tunnel?")
if not(has_pobj_str("to")):
	caller.write("Where do you want to dig %s to?" % get_dobj_str() )
	
connection = get_obj(get_pobj_str("to"))
room = caller.get_location()
direction = get_dobj_str()

if not(room.has_property("exits")):
	room.add_property("exits", {}, caller)
exits = room.get_property("exits", False)
if(direction in exits):
	caller.write("There is already an exit in that direction.")
	return
exits[direction.lower()] = connection
room.set_property("exits", exits)
room.notify()
caller.write("You created an exit to %s in the '%s' direction." % (str(connection), direction) )	 
