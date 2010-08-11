# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if(has_pobj("on")):
	obj = get_pobj("on")
else:
	obj = get_obj(get_pobj_str("on"))

edit_verb(caller, obj, get_dobj_str())

