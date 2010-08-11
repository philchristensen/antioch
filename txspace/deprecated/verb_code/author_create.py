# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("What do you want to create?", is_error=True)
	return
obj = new_obj(get_dobj_str())
obj.set_location(caller.get_location())
caller.get_location().notify()
caller.write("You have created " + obj)
