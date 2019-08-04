#!antioch verb dig "author class" --ability --owner "wizard" \
# --access-group allow:everyone:execute

room_class = get_object('room class')
direction = get_dobj_str()

room = create_object(get_pobj_str('to'))
room.add_parent(room_class)
room.set_location(None)

if(here.has_property('exits')):
    exits = here['exits'].value
    exits[direction] = room
    here['exits'].value = exits
else:
    here.add_property('exits').value = {direction : room}

write(caller, "You dug a new room %s in the %s" % (room, direction))
