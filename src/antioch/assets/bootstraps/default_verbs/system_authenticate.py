#!antioch

username = args[0]
password = args[1]

if(username != 'guest'):
	return None

room = get_object("The Lobby")
player_class = get_object('player class')

# get the list of available guest names, which
# also sets the total number of possible guests
if('guest_names' in system):
	guest_names = system['guest_names'].value
else:
	guest_names = system.add_property('guest_names').value = [
		'Red Guest', 'Blue Guest', 'Yellow Guest',
		'Green Guest', 'Orange Guest', 'Purple Guest',
	]

# get the registry where we keep the guest objects
if('guestbook' in system):
	guestbook = system['guestbook'].value
else:
	guestbook = system.add_property('guestbook').value = dict()

# the first time, we will create guest objects
# for all guest names
guest_object = None
for name in guest_names:
	if(name in guestbook and not guestbook[name].is_connected_player()):
		guest_object = guestbook[name]
		break
	elif(count_named(name) == 0):
		guest_object = guestbook[name] = create_object(name, unique_name=True)
		guest_object.location = room
		guest_object.set_player(True)
		guest_object.add_parent(player_class)
		guest_object.set_owner(guest_object)
		break
else:
	print "[guests] rejected, too many guests"
	raise PermissionError("Sorry, there are too many guests already.")

system['guestbook'].value = guestbook

return guest_object
