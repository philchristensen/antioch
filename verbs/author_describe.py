#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: author_describe.py 33 2006-04-16 20:54:45Z phil $
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("What do you want to describe?")
	return
if not(has_pobj_str("as")):
	caller.write("How do you want to describe %s?" % get_dobj_str() )
	return

item = get_dobj()
description = get_pobj_str('as')

if not(item.has_property('description', recurse=False)):
	item.add_property('description', description, caller)
else:
	item.set_property('description', description)

item.notify()
caller.write("Description of %s set to '%s'" % (str(item), description) )
