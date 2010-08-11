# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

# def load_verb(self, obj, verb_path, verb_names, owner, **kwargs):
# @load verb on obj with verb_path as ability, method

if not(has_dobj_str()):
	caller.write("What verb do you want to load?", is_error=True)
	return
if not(has_pobj_str('on')):
	caller.write("On what object should that verb be defined?", is_error=True)
	return
if not(has_pobj_str('with')):
	caller.write("With what path should should we load the verb?", is_error=True)
	return

if(has_pobj('on')):
	obj = get_pobj('on')
else:
	obj = get_obj(get_pobj_str('on'))

verb_path = get_pobj_str('with')

verb_name = get_dobj_str()
if(verb_name.find(',') != -1):
	verb_names = verb_name.split(',')
	for index in range(len(verb_names)):
		verb_names[index] = verb_names[index].strip()
else:
	verb_names = [verb_name]

args = {}
owner = caller

if(has_pobj_str('as')):
	arguments = get_pobj_str('as').split(',')
	for index in range(len(arguments)):
		temp = arguments[index].strip()
		if(temp.find('=') == -1):
			args[temp] = 'True'
		else:
			key,value = temp.split('=')
			if(key == 'owner'):
				owner = get_obj(value)
			else:
				args[key] = value

load_verb(obj, verb_path, verb_names, owner, **args)

caller.write("The verb %s was sucessfully loaded on %s." % (verb_name, str(obj)))