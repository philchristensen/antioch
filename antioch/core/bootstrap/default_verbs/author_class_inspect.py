#!antioch

if(has_dobj()):
    obj = get_dobj()
else:
    obj = get_object(get_dobj_str())

details = obj.get_details()
ancestors = obj.get_ancestors()

output = '<div class="inspection">'
output += '<h3 class="name">%s</h3>' % details['name']
output += '<ul>'
output += '<li><b>Ancestors:</b> %s</li>' % ', '.join(str(x) for x in ancestors)
output += '<li><b>Location:</b> %s</li>' % details['location']
output += '<li><b>Contents:</b> %s</li>' % ', '.join(str(x) for x in obj.contents)
output += '<li><b>Owner:</b> %s</li>' % details['owner']

def format_verb(v):
    klass = 'info' if v['ability'] else 'primary'
    return (klass, "%(name)s%(method)s" % dict(
        name = v['names'],
        method = '()' if v['method'] else ''
    ))

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

output += '</ul>'

output += '</div>'

write(caller, output, escape_html=False)