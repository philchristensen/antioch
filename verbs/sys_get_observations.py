#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: sys_get_observations.py 154 2007-02-11 01:20:42Z phil $
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
	contents.append(item.get_name())
obs[u'contents'] = contents
obs[u'id'] = unicode(obj)
return obs
