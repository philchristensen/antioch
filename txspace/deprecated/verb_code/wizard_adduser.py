# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("Usage:")
	caller.write("	 @adduser [name]")
	return

user = new_obj(get_dobj_str())
user.set_player()

player_class = system.get_property('default_player_class')
if(player_class):
	user.set_parent(player_class)
user.set_owner(user)
user.set_location(caller.get_location())
caller.write("The user %s has been created. Now set a password with @passwd." % [str(user)])
