# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if(this.is_connected_player()):
	text = '%s says, "%s"' % (args[0].get_name(), args[1])
	if(args[2]):
		text += " to you."
	this.write(text)
