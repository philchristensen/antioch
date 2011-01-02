#!antioch

if not(has_dobj_str() and has_pobj_str('for')):
	raise UsageError('Usage: @register <new-name> for <email-address>')

player_name = get_dobj_str()
player_email = get_pobj_str('for')

matches = get_object(player_name, return_list=True)
if(matches):
	raise UsageError("There's already an object by the name '%s'. Player names must be unique." % player_name)

request_account(player_name, player_email)

print "A verification email has been sent to %s, containing a URL you must visit to continue." % player_email