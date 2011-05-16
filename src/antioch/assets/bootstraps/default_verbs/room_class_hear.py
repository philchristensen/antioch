#!antioch

source, msg = args

for target in this.contents:
	to_target = '<span class="target-heard-public">%s: %s</span>' % (source.name, msg)
	if(target != source):
		write(target, to_target, escape_html=False)