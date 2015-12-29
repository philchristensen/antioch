#!antioch

if not(has_dobj_str()):
    write(caller, "Where do you want to go?", is_error=True)
    return

if not(caller.location.has_property('exits')):
    write(caller, "You can't go that way.", is_error=True)
    return

exits = caller.location['exits'].value
direction = get_dobj_str()

if(direction not in exits):
    print "You can't go that way."
    return

caller.set_location(exits[direction])
caller.look()
