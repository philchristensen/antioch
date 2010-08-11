# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if(this.has_readable_property('ban_list')):
	connecting_host = args[0];
	ban_list = this.get_property('ban_list')
	
	if(connecting_host in ban_list):
		return False

return True