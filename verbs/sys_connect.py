#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: sys_connect.py 159 2007-02-14 03:47:03Z phil $
#
# See LICENSE for details

if(this.has_readable_property('ban_list')):
	connecting_host = args[0];
	ban_list = this.get_property('ban_list')
	
	if(connecting_host in ban_list):
		return False

return True