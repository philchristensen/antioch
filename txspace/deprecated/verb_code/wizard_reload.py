# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# 
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("What verb do you want to reload?", is_error=True)
	return
if not(has_pobj_str('on')):
	caller.write("Where is that verb defined?", is_error=True)
	return

verb_name = get_dobj_str()
if(has_pobj('on')):
	target = get_pobj('on')
else:
	target = get_obj(get_pobj_str('on'))

origin = target.get_ancestor_with(verb_name)

if not(origin):
	caller.write("The verb %s is not defined on %s or any of its ancestors." % (verb_name, str(target)), is_error=True)
	return

reload_verb(origin, verb_name)

caller.write("The verb %s was sucessfully reloaded on %s." % (verb_name, str(origin)), is_error=True)