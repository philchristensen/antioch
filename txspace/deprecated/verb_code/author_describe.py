# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("What do you want to describe?", is_error=True)
	return
if not(has_pobj_str("as")):
	caller.write("How do you want to describe %s?" % get_dobj_str(), is_error=True)
	return

item = get_dobj()
description = get_pobj_str('as')

if not(item.has_property('description', recurse=False)):
	item.add_property('description', description)
else:
	item.set_property('description', description)

item.notify()
caller.write("Description of %s set to '%s'" % (str(item), description) )
