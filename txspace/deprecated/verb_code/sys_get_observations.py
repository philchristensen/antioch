# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

obj = args[0]
obs = {u'name':obj.get_name()}
if(obj.has_property('description')):
	obs[u'description'] = obj.get_property('description')
else:
	obs[u'description'] = u"There doesn't seem to be anything special about %s." % obs['name']
if(obj.has_property('image')):
	obs[u'image'] = obj.get_property('image')
if(obj.has_property('soundtrack')):
	obs[u'soundtrack'] = obj.get_property('soundtrack')

contents = []
for item in obj.get_contents():
	details = {}
	details[u'type'] = item.get_entity_type()
	details[u'name'] = item.get_name()
	if(item.has_property('image')):
		details[u'image'] =  obj.get_property('image')
	contents.append(details)
obs[u'contents'] = contents

obs[u'id'] = unicode(obj)

return obs
