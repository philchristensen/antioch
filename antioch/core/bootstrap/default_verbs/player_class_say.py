#!antioch

msg = get_dobj_str()
if(has_pobj_str('to')):
    subject = get_pobj('to')
    msg_type = 'private'
else:
    subject = caller.location
    msg_type = 'public'

to_source = '<span class="source-said-%s">%s%s: %s</span>' % (
    msg_type,
    ['', '@'][msg_type=='private'],
    subject.name,
    msg
)
write(caller, to_source, escape_html=False)

subject.hear(caller, msg)