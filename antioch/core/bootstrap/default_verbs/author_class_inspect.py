#!antioch

if not has_pobj_str('on'):
    stype = 'object'
    if(has_dobj()):
        subject = get_dobj()
    else:
        subject = get_object(get_dobj_str())
else:
    if(has_pobj('on')):
        origin = get_pobj('on')
    else:
        origin = get_object(get_pobj_str('on'))
    
    subjects = get_dobj_str().split(' ', 1)
    if(len(subjects) == 2):
        stype, name = subjects
    else:
        stype = None
        name = subjects[0]
    
    if(stype == 'verb'):
        subject = origin.get_verb(name)
        if subject is None:
            raise NoSuchVerbError(name)
    elif(stype in ('property', 'prop', 'value', 'val')):
        subject = origin.get_property(name)
        if subject is None:
            raise NoSuchPropertyError(name, origin)
    else:
        subject = origin.get_verb(name) or origin.get_property(name)
        if subject is None:
            raise NoSuchPropertyError(name, origin)

def format_verb(v):
    klass = 'info' if v['ability'] else 'primary'
    return (klass, "%(name)s%(method)s" % dict(
        name = v['names'],
        method = '()' if v['method'] else ''
    ))

details = subject.get_details()
stype = subject.get_type()
if stype == 'verb':
    sname = ', '.join(details['names'])
else:
    sname = details['name']
output = '<div class="inspection">'
output += '<h3 class="name">%s</h3>' % sname
output += '<ul>'
output += '<li><b>Owner:</b> %s</li>' % details['owner']

if(stype == 'object'):
    ancestors = subject.get_ancestors()
    output += '<li><b>Ancestors:</b> %s</li>' % ', '.join(str(x) for x in ancestors)
    output += '<li><b>Location:</b> %s</li>' % details['location']
    output += '<li><b>Contents:</b> %s</li>' % ', '.join(str(x) for x in subject.contents)

    output += '<li><b>Verbs:</b><ul>'
    for verb in details['verbs']:
        output += '<li><a href="#" class="badge badge-pill badge-%s">%s</a></li>' % format_verb(verb)
    for obj in ancestors:
        d = obj.get_details()
        if(d['verbs']):
            output += "<li><small>%s</small><ul class=\"inherited\">" % d['name']
            for verb in d['verbs']:
                output += '<li><a href="#" class="badge badge-pill badge-%s">%s</a></li>' % format_verb(verb)
            output += "</ul></li>"
    output += '</ul></li>'

    output += '<li><b>Properties:</b><ul>'
    for prop in details['properties']:
        output += '<li><a href="#" class="badge badge-pill badge-primary">%s</a></li>' % prop['name']
    for obj in ancestors:
        d = obj.get_details()
        if(d['properties']):
            output += "<li><small>%s</small><ul class=\"inherited\">" % d['name']
            for prop in d['properties']:
                output += '<li><a href="#" class="badge badge-pill badge-primary">%s</a></li>' % prop['name']
            output += "</ul></li>"
    output += '</ul></li>'
elif(stype == 'verb'):
    output += '<li><b>Type:</b> %s</li>' % details['exec_type']
elif(stype in ('property', 'prop', 'value', 'val')):
    output += '<li><b>Type:</b> %s</li>' % details['type']

output += '</ul>'

output += '</div>'

write(caller, output, escape_html=False)