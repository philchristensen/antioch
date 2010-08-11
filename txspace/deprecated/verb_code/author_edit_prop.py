# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("What property do you want to edit?", is_error=True)
	return
if not(has_pobj("on")):
	caller.write("Edit property '%s' on what?" % get_dobj_str())
	return

if(has_pobj("on")):
	obj = get_pobj("on")
else:
	obj = get_obj(get_pobj_str("on"))

edit_property(caller, obj, get_dobj_str())
