#!antioch

obj_name = get_dobj_str()
obj_parent = None

if(has_pobj_str('from')):
    obj_parent = get_pobj_str('from')

unique_name = False
if(has_pobj_str('with')):
    if(get_pobj_str('with') == 'unique name'):
        unique_name = True
    else:
        write(caller, "I don't know how to make an object with `%s`" % get_pobj_str('with'), True)
        return

obj = create_object(obj_name, unique_name)
if(obj_parent):
    obj.add_parent(obj_parent)
obj.set_location(caller.location)

write(caller, "Made %r for you." % obj_name)
