# private:
# '<span style="color: #ab3e4c;">%s: %s</span>' % (name, msg), False, False\
# '<span style="color: #477a67;">@%s: %s</span>' % (subjects[0].get_name(), msg), False, False

# public:
# '<span style="color: #7f91c8;">%s: %s</span>' % (name, msg), False, False
# '<span style="color: #477a67;">@%s: %s</span>' % (caller.location.get_name(), msg), False, False

caller, msg = args
public = kwargs.get('public', False)
target = this

if(public):
	if(target == caller):
		output = '<span style="color: #477a67;">@%s: %s</span>' % (caller.location.name, msg)
	else:
		output = '<span style="color: #7f91c8;">%s: %s</span>' % (caller.name, msg)
else:
	if(target == caller):
		output = '<span style="color: #477a67;">@%s: %s</span>' % (caller.name, msg)
	else:
		output = '<span style="color: #ab3e4c;">%s: %s</span>' % (caller.name, msg)

write(target, output, escape_html=False)
