#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: author_create.py 184 2007-03-04 18:54:05Z phil $
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("What do you want to create?")
	return
obj = new_obj(get_dobj_str())
obj.set_location(caller.get_location())
caller.get_location().notify()
caller.write("You have created " + obj)
