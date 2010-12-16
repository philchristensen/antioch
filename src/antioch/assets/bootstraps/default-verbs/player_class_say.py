#!antioch

if(has_pobj_str('to')):
	subjects = [get_pobj('to')]
else:
	subjects = [x for x in caller.location.get_contents() if x.is_connected_player()]

name = caller.get_name()
msg = get_dobj_str()
if(len(subjects) == 1):
	write(subjects[0], '<span style="color: #ab3e4c;">%s: %s</span>' % (name, msg), False, False)
	write(caller, '<span style="color: #477a67;">@%s: %s</span>' % (subjects[0].get_name(), msg), False, False)
else:
	for subject in subjects:
		if(subject == caller):
			continue
		write(subject, '<span style="color: #7f91c8;">%s: %s</span>' % (name, msg), False, False)
	write(caller, '<span style="color: #477a67;">@%s: %s</span>' % (caller.location.get_name(), msg), False, False)
