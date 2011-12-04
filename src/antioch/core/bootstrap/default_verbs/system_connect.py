#!antioch

if('banlist' in this):
	banlist = this['banlist'].value
	if(args[0] in banlist):
		raise PermissionError("The IP address %s has been banned." % args[0])
