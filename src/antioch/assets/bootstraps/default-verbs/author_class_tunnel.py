#!antioch

room_class = get_object('room class')
direction = get_dobj_str()

room = get_object(get_pobj_str('to'))

if(here.has_property('exits')):
	exits = here['exits'].value
	exits[direction] = room
	here['exits'].value = exits
else:
	here.add_property('exits').value = {direction : room}

write(caller, "You dug a tunnel %s to %s" % (direction, room))
