# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if(has_pobj("to")):
	subject = get_pobj("to")
	if(subject.has_verb("hear")):
		subject.call_verb("hear", caller, get_dobj_str(), True)
		caller.write('You say, "%s" to %s.' % (get_dobj_str(), subject.get_name()))
else:
	for item in caller.get_location().get_contents():
		if(item.has_verb("hear") and item is not caller):
			item.call_verb("hear", caller, get_dobj_str(), False)
	caller.write('You say, "%s"' % (get_dobj_str()))
