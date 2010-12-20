#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: author_alias.py 159 2007-02-14 03:47:03Z phil $
# 
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("What do you want to create an alias for?")
	return
if not(has_pobj_str('to')):
	caller.write("What do you want to call it?")
	return

obj = get_dobj()
if(obj.has_property('aliases')):
	aliases = obj.get_property('aliases')
else:
	aliases = []
if(get_pobj_str('to') not in aliases):
	aliases.append(get_pobj_str('to'))

if(obj.has_property('aliases')):
	obj.set_property('aliases', aliases)
else:
	obj.add_property('aliases', aliases, caller)