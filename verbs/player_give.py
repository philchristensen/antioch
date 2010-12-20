#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: player_give.py 33 2006-04-16 20:54:45Z phil $
#
# See LICENSE for details

if(words[0] == 'give'):
	get_dobj().set_location(get_pobj("to"))
elif(words[0] == 'put'):
	get_dobj().set_location(get_pobj("in"))
else:
	get_dobj().set_location(caller.get_location())
