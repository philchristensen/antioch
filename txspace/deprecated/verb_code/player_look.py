# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if(has_dobj_str()):
	target = get_dobj()
elif(has_pobj_str("at")):
	target = get_pobj("at")
else:
	target = caller.get_location()
if(target.is_connected_player()):
	target.write(caller.get_name() + " looks at you.")
caller.set_observing(target)
