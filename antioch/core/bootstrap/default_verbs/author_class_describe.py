#!antioch

if not(has_dobj_str()):
    write(caller, 'What do you want to describe?', is_error=True)
    return
if not(has_pobj_str('as')):
    write(caller, 'What do you want to describe that as?', is_error=True)
    return

subject = get_dobj()
if(subject.has_property('description')):
    description = subject.get_property('description')
else:
    description = subject.add_property('description')

description.value = get_pobj_str('as')
print('Description set for %s' % subject)
subject.notify_observers()
