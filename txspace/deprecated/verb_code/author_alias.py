# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# 
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("What do you want to create an alias to?", is_error=True)
	return
if not(has_pobj_str('to')):
	caller.write("What do you want to call it?", is_error=True)
	return

obj = get_dobj()
if(obj.has_property('aliases')):
	aliases = obj.get_property('aliases')
else:
	aliases = []
if(get_pobj_str('to') not in aliases):
	aliases.append(get_pobj_str('to'))

if(obj.has_property('aliases')):
	obj.set_property('aliases', aliases)
else:
	obj.add_property('aliases', aliases)

caller.write("Sucessfully created alias %s to %s." % (get_pobj_str('to'), obj))