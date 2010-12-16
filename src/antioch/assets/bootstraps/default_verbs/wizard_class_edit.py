#!antioch

if not has_pobj_str('on'):
	if(has_dobj()):
		subject = get_dobj()
	else:
		subject = get_object(get_dobj_str())
else:
	if(has_pobj('on')):
		origin = get_pobj('on')
	else:
		origin = get_object(get_pobj_str('on'))
	
	subjects = get_dobj_str().split(' ', 1)
	if(len(subjects) == 2):
		stype, name = subjects
	else:
		stype = None
		name = subjects[0]
	
	if(stype == 'verb'):
		subject = origin.get_verb(name)
		if subject is None:
			raise NoSuchVerbError(name)
	elif(stype in ('property', 'prop', 'value', 'val')):
		subject = origin.get_property(name)
		if subject is None:
			raise NoSuchPropertyError(name, origin)
	else:
		subject = origin.get_verb(name) or origin.get_property(name)
		if subject is None:
			raise NoSuchPropertyError(name, origin)

edit(subject)
