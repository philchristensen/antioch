#!antioch

if('last_location' in caller):
    caller['last_location'].value = caller.location
else:
    caller.add_property('last_location', value=caller.location)

broadcast("%s vanishes, as if suddenly dead of boredom." % caller.get_name())

caller.set_location(None)