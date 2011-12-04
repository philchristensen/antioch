#!antioch

if(runtype == 'method'):
	user = get_object(args[0])
	if(args[1] == 'validate'):
		#TODO validate passwd
		if(user.validate_password(args[2])):
			ask('Please enter the new password:', self, user.get_id(), 'change')
		else:
			write(caller, "The password is incorrect. Please enter your *current* password for " + str(user))
	else:
		user.set_player(passwd=args[2])
		print "Changed password for " + str(user)
	return

if(has_dobj_str()):
	user = get_dobj()
else:
	user = caller

if(user == caller):
	ask('Please enter your current password:', self, user.get_id(), 'validate')
else:
	ask('Please enter the new password:', self, user.get_id(), 'change')
