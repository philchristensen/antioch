options = args[0]

user = create_object(options['name'])
user.set_player(True, passwd=options.get('passwd', None))

parent = options.get('parent', get_object('player class'))
user.add_parent(parent)
user.owner = options.get('owner', user)
user.location = options.get('location', None)

return user