#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: author_alias-exit.py 159 2007-02-14 03:47:03Z phil $
# 
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("What do you want to call this exit?")
	return
if not(has_pobj_str('to')):
	caller.write("What exit do you want this to be an alias for?")
	return

if(here.has_property('exit_aliases')):
	aliases = here.get_property('exit_aliases')
else:
	aliases = {}

aliases[get_dobj_str().lower()] = get_pobj_str('to').lower()

if(here.has_property('exit_aliases')):
	here.set_property('exit_aliases', aliases)
else:
	here.add_property('exit_aliases', aliases, caller)
	
caller.write("Sucessfully created alias %s to exit %s." % (get_dobj_str(), get_pobj_str('to')))