# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if(has_dobj()):
	edit_entity(caller, get_dobj())
else:
	edit_entity(caller, get_obj(get_dobj_str()))
