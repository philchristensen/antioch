# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

def alight(item):
	for thing in item.get_contents():
		if(thing.has_property("lit") and thing.get_property("lit")):
			return True
		elif(thing.get_contents()):
			if alight(thing):
				return True
	return False
	
obs = {}

if(this.has_property('soundtrack')):
	obs[u'soundtrack'] = this.get_property('soundtrack')

if(this.has_property('dark') and this.get_property('dark') and (not alight(this))):
	obs[u'name'] = u"a very dark place..."
	obs[u'description'] = u"darkness warshed over the dude. darker'n a black steer's tuckus on a moonless prarie night...there was no bottom..."
	obs[u'contents'] = []
else:
	obs[u'name'] = this.get_name()
	description = ''
	if(this.has_property('image')):
		description += u'<img src="' + this.get_property('image') + '" border="0"/>'
	if(this.has_property('description')):
		description += u'<p>' + this.get_property('description') + '</p>'
	else:
		description += u"<p>Nothing much to see here.</p>"
	if(this.has_property('exits')):
		exits = this.get_property('exits')
		description += u"<BR><BR><B>Obvious Exits:</B> " + ', '.join(exits.keys())
	
	obs[u'description'] = description
	
	if(this.has_property('image')):
		obs[u'image'] = this.get_property('image')
	contents = []
	for item in this.get_contents():
		details = {}
		if((not item.has_property("visible")) or item.get_property("visible")):
			details[u'type'] = item.get_entity_type()
			details[u'name'] = item.get_name()
			if(item.has_property('image')):
				details[u'image'] = item.get_property('image')
			if(item.has_property("mood")):
				details[u'mood'] =  item.get_property("mood")
			contents.append(details)
	obs[u'contents'] = contents

obs[u'id'] = unicode(this)
return obs