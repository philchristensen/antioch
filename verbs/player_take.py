#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: player_take.py 33 2006-04-16 20:54:45Z phil $
#
# See LICENSE for details

if(has_pobj_str("from")):
	found = get_pobj("from").find(get_dobj_str())
	found.set_location(caller)
else:
	get_dobj().set_location(caller)
