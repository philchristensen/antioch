#!antioch

if(has_pobj_str('to')):
	subjects = [get_pobj('to'), caller]
	public = False
else:
	subjects = [x for x in caller.location.get_contents()]
	public = True

name = caller.get_name()
msg = get_dobj_str()

[s.hear(caller, msg, public=public)
	for s in subjects
	if(s.has_verb('hear'))
]