#!antioch

if('ban_list' in this):
	ban_list = this['ban_list'].value
	if(args[0] in ban_list):
		raise PermissionError("The IP address %s has been banned.")
