#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: programmer_edit_verb.py 184 2007-03-04 18:54:05Z phil $
#
# See LICENSE for details

if(has_pobj("on")):
	obj = get_pobj("on")
else:
	obj = get_obj(get_pobj_str("on"))

edit_verb(caller, obj, get_dobj_str())

