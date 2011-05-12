#!antioch

source, msg = args

to_target = '<span class="target-heard-private">%s: %s</span>' % (source.name, msg)
write(this, to_target, escape_html=False)