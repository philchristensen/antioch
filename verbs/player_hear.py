#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: player_hear.py 33 2006-04-16 20:54:45Z phil $
#
# See LICENSE for details

if(this.is_connected_player()):
	text = '%s says, "%s"' % (args[0].get_name(), args[1])
	if(args[2]):
		text += " to you."
	this.write(text)
