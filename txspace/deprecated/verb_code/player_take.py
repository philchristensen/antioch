# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if(has_pobj_str("from")):
	found = get_pobj("from").find(get_dobj_str())
	found.set_location(caller)
else:
	get_dobj().set_location(caller)
