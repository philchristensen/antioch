# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("In what direction do you want to tunnel?", is_error=True)
if not(has_pobj_str("to")):
	caller.write("Where do you want to dig %s to?" % get_dobj_str(), is_error=True)
	
connection = get_obj(get_pobj_str("to"))
room = caller.get_location()
direction = get_dobj_str()

if not(room.has_property("exits")):
	room.add_property("exits", {}, acl_config=readable_property_acl)
exits = room.get_property("exits", False)
if(direction in exits):
	caller.write("There is already an exit in that direction.", is_error=True)
	return
exits[direction.lower()] = connection
room.set_property("exits", exits)
room.notify()
caller.write("You created an exit to %s in the '%s' direction." % (str(connection), direction) )	 
