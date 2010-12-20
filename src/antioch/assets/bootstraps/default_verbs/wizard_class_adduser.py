#!antioch

if not(has_dobj_str()):
	caller.write("Usage: @adduser [name]", is_error=True)
	return

user = create_object(get_dobj_str())
user.set_player(True)

player_class = system.get_property('default_player_class', None).value
if(player_class):
	user.add_parent(player_class)

user.owner = user
user.location = caller.location

caller.write("The user %s has been created. Now set a password with @passwd." % [str(user)])
