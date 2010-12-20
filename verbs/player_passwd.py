#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: player_passwd.py 33 2006-04-16 20:54:45Z phil $
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("Who's password do you want to set?")
	return
if not(has_pobj_str("to")):
	caller.write("What do you want the password to be?")

def admin_passwd():
	dobj = get_dobj()
	if(dobj.has_property('password', False)):
		get_dobj().add_property("passwd", get_pobj_str("to"))
	else:
		owner = system.get_property('default_owner')
		get_dobj().add_property("passwd", get_pobj_str("to"), owner)

sudo(admin_passwd)
caller.write("Password set.")
