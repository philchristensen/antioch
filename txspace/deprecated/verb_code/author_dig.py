# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("In what direction do you want to dig?", is_error=True)
	return
if not(has_pobj_str("to")):
	caller.write("Where do you want to dig %s to?" % get_dobj_str(), is_error=True)
	return

connection = new_obj(get_pobj_str("to"))
connection.set_parent(system.get_property('default_room_class'))
room = caller.get_location()
direction = get_dobj_str()

try:
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
except PermissionError, e:
	caller.write("Your room was created, but you do not have permission to create an exit to it from here.");
