#!antioch

if(runtype == 'method'):
    obj = args[0] if args else caller.location
    target = this
else:
    if(has_dobj_str()):
        obj = get_dobj()
        target = caller
    else:
        obj = caller.get_location()
        target = caller

current = target.get_observing()
if(current and current is not obj):
    current.remove_observer(target)
if(obj and obj is not current):
    obj.add_observer(target)

import hashlib
def gravatar_url(email):
    m = hashlib.md5()
    m.update(email.strip().lower())
    return 'http://www.gravatar.com/avatar/%s.jpg?d=mm' % m.hexdigest()

if(obj):
    observations = dict(
        id                = obj.get_id(),
        name            = obj.get_name(),
        location_id        = str(obj.get_location()) or 0,
        description        = obj.get('description', 'Nothing much to see here.').value,
        contents        = [
            dict(
                type    = item.is_player(),
                name    = item.get_name(),
                image    = gravatar_url(item['gravatar_id'].value) if 'gravatar_id' in item else None,
                mood    = item.get('mood', None).value,
            ) for item in obj.get_contents() if item.get('visible', True).value
        ],
    )
    if(obj.is_connected_player() and caller != target):
        write(obj, "%s looks at you" % target.get_name())
else:
    observations = dict(
        id                = None,
        name            = 'The Void',
        location_id        = None,
        description        = 'A featureless expanse of gray nothingness.',
        contents        = [],
    )

if(obj.id == caller.location.id):
    observe(target, observations)
else:
    output = '<h3 class="name">%s</h3>' % observations['name']
    output = output + '<p class="lead description">%s</p>' % observations['description']
    write(target, output, escape_html=False)