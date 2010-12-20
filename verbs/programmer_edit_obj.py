#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: programmer_edit_obj.py 184 2007-03-04 18:54:05Z phil $
#
# See LICENSE for details

if(has_dobj()):
	edit_entity(caller, get_dobj())
else:
	edit_entity(caller, get_obj(get_dobj_str()))
