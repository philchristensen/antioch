#!antioch

if not(has_dobj_str() and has_pobj_str('for')):
	raise UsageError("Usage: @adduser [name] for [email]")

hammer = get_object('wizard hammer')
user = hammer.add_user(dict(
	name		= get_dobj_str(),
	location	= caller.location,
))

write(caller, "The user %s has been created. Now set a password with @passwd." % str(user))
