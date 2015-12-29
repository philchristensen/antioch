#!antioch

if not(has_dobj_str()):
    write(caller, "What property do you wish to set?", is_error=True)
    return

if not(has_pobj_str('on')):
    write(caller, "Where do you want to set the %r property?" % get_dobj_str(), is_error=True)
    return

if not(has_pobj_str('to')):
    write(caller, "What do you want to set %r to?" % get_dobj_str(), is_error=True)
    return

prop_name = get_dobj_str()
subject = get_pobj('on')
value = get_pobj_str('to')

if(subject.has_property(prop_name)):
    subject.get_property(prop_name).value = value
else:
    subject.add_property(prop_name).value = value
