#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: wizard_reload.py 184 2007-03-04 18:54:05Z phil $
# 
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("What verb do you want to reload?")
	return
if not(has_pobj_str('on')):
	caller.write("Where is that verb defined?")
	return

verb_name = get_dobj_str()
if(has_pobj('on')):
	target = get_pobj('on')
else:
	target = get_obj(get_pobj_str('on'))

origin = target.get_ancestor_with(verb_name)

if not(origin):
	caller.write("The verb %s is not defined on %s or any of its ancestors." % (verb_name, str(target)))
	return

reload_verb(origin, verb_name)

caller.write("The verb %s was sucessfully reloaded on %s." % (verb_name, str(origin)))