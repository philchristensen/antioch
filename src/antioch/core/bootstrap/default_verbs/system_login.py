#!antioch

if('last_location' in caller):
	caller.location = caller['last_location'].value
	broadcast("%s appears suddenly, looking refreshed and rejuvenated." % caller.get_name())