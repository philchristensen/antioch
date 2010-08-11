# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
<EntityList>
<Entity uid="1" name="EntityName" unique="1" type="0" parent="" location="" owner="">
<ACL>allow owners anything
allow wizards anything
allow everyone get_children
allow everyone get_contents
...
...</ACL>
<Property name="passwd" type="" owner="">
<ACL>allow owners anything
allow wizards anything</ACL>
<Value>test123</Value>
</Property>
<Verb name="go" owner="" ability="1" method="0">
<ACL>allow owners anything
allow wizards anything</ACL>
<Code>
...
...
</Code>
<Alias>walk</Alias>
</Verb>
</Entity>
</EntityList>
"""
import os, copy

from xml.parsers import expat

from txspace import entity, security, prop, verb
from txspace.security import Q

entity_start = u'<Entity uid="%s" name="%s" unique="%d" type="%d" parent="%d" location="%d" owner="%d">'
verb_start = u'<Verb name="%s" owner="%d" ability="%d" method="%d">'
prop_start = u'<Property name="%s" type="%d" owner="%d">'

def save(reg, path):
	datafile = file(path, 'w')
	export(reg, datafile)
	datafile.close()

def load(reg, path):
	if not(os.access(path, os.R_OK)):
		return False
	datafile = file(path)
	ingest(reg, datafile.read())
	datafile.close()
	
	return True
	
def rotate_datafile(path):
	if(os.access(path + '.shutdown', os.F_OK)):
		if(os.access(path, os.F_OK)):
			if(os.stat(path + '.shutdown').st_mtime >= os.stat(path).st_mtime):
				os.rename(path, path + '.bak')
		os.rename(path + '.shutdown', path)
	
	if(not path):
		save_path = 'universe.xml'
	else:
		save_path = path + '.shutdown'
	
	return save_path

def export(registry, datafile=None):
	result = u'<EntityList>'
	for item in registry._objects:
		result += _entity_as_xml(registry, item)
		if(datafile):
			datafile.write(result)
			result = ''
	result += u'</EntityList>'
	if(datafile):
		datafile.write(result)
		return True
	else:
		return result

def ingest(registry, xml):
	parser = RegistryParser(registry)
	parser.parse(xml)

class RegistryParser:
	def __init__(self, registry):
		self.parser = expat.ParserCreate()
		self.parser.StartElementHandler = self._start_element
		self.parser.EndElementHandler = self._end_element
		self.parser.CharacterDataHandler = self._char_data
		self.registry = registry
		self.cdata_buffer = ''
	
	def parse(self, data):
		if(isinstance(data, file)):
			self.parser.ParseFile(data)
		else:
			self.parser.Parse(data)
	
	def _start_element(self, name, attribs):
		if(name in ('Entity', 'Verb', 'Property')):
			self.parsing_element = name
		
		if(name == 'EntityList'):
			self.ids = {}
			self.objects = []
			self.unique_names = {}
			self.missing_entities = []
		elif(name == 'Entity'):
			self.current_entity = self._get_entity_by_id(attribs['uid'], unescape(attribs['name']), bool(int(attribs['unique'])))
			# an object shouldn't be added to the list until it's done
			#self.objects.append(self.current_entity)
			
			if(attribs['parent']):
				self.current_entity.set_parent(Q, self._get_entity_by_id(attribs['parent']))
			if(attribs['location']):
				self.current_entity.set_location(Q, self._get_entity_by_id(attribs['location']))
			if(attribs['owner']):
				self.current_entity.set_owner(Q, self._get_entity_by_id(attribs['owner']))
			
			self.current_entity._vitals['entity_type'] = int(attribs['type'])
		elif(name == 'Property'):
			#<Property name="passwd" type="" owner="">
			owner = self._get_entity_by_id(attribs['owner'])
			self.current_prop = prop.Property(Q, None, **dict(
				owner		= owner,
				origin		= self.current_entity,
				eval_type	= attribs['type'],
			))
			self.current_prop_name = unescape(attribs['name'])
		elif(name == 'Verb'):
			owner = self._get_entity_by_id(attribs['owner'])
			self.current_verb = verb.Verb(Q, '', [attribs['name']], **dict(
				owner		= owner,
				origin		= self.current_entity,
				is_ability	= bool(int(attribs['ability'])),
				is_method	= bool(int(attribs['method'])),
			))
	
	def _char_data(self, data):
		self.cdata_buffer += unescape(data)
	
	def _end_element(self, name):
		data = self.cdata_buffer
		# we may not want to do this....
		# i don't think it would be a problem unless we start
		# intermixing cdata with tags
		self.cdata_buffer = ''
		if(name in ('Entity', 'Verb', 'Property')):
			self.parsing_element = None
		
		if(name == 'EntityList'):
			# after loading everything, import it into the
			# registry...
			for obj in self.objects:
				#print 'PUT: ' + str(obj) + " unique: " +  str(obj._name in self.unique_names)
				self.registry.put(obj, obj._name in self.unique_names)
		elif(name == 'Entity'):
			self.objects.append(self.current_entity)
			self.current_entity = None
		elif(name == 'Property'):
			self.current_entity._vdict[self.current_prop_name] = self.current_prop
			self.current_prop = None
			self.current_prop_name = None
		elif(name == 'Verb'):
			for name in self.current_verb.get_names(Q):
				#print 'adding verb ' + name + ' to ' + str(self.current_entity)
				self.current_entity._vdict[name] = self.current_verb
			self.current_verb = None
		elif(name == 'ACL'):
			#print 'got cdata for ACL: ' + data
			if(self.parsing_element == 'Entity'):
				obj = self.current_entity
			elif(self.parsing_element == 'Verb'):
				obj = self.current_verb
			elif(self.parsing_element == 'Property'):
				obj = self.current_prop
			else:
				raise TypeError('Invalid parsing_element "%s"' % self.parsing_element)
			obj._vitals['acl'] = []
			perms = data.split("\n")
			for perm in perms:
				if not(perm):
					continue
				parts = perm.split(' ')
				if(parts[0] == 'allow'):
					security.allow(' '.join(parts[1:len(parts)-1]), parts[len(parts)-1], obj)
				elif(parts[0] == 'deny'):
					security.deny(' '.join(parts[1:len(parts)-1]), parts[len(parts)-1], obj)
				else:
					raise TypeError('Invalid ACL state "%s"' % parts[0])
		elif(name == 'Value'):
			if(self.current_prop.get_eval_type(Q) == prop.EVAL_PYTHON):
				self.current_prop.set_value(Q, data, True)
			else:
				self.current_prop.set_value(Q, data)
		elif(name == 'Code'):
			self.current_verb._vitals['code'] = data
		elif(name == 'Alias'):
			names = self.current_verb.get_names(Q)
			names.append(data)
			self.current_verb.set_names(Q, names)
	
	def _get_entity_by_id(self, uid, name=None, unique=False):
		if(int(uid) == -1):
			return None
		if(uid in self.ids):
			ent = self.ids[uid]
			if((not ent._name) and name):
				if(name in self.unique_names):
					raise ValueError("unique name error")
				#print 'adding ' + name + ' to unique list'
				ent._name = name
				self.unique_names[name] = ent
			if(ent in self.missing_entities):
				self.missing_entities.remove(ent)
		else:
			ent = entity.Entity(self.registry, name)
			if(unique and name):
				if(name in self.unique_names):
					raise ValueError("unique name error")
				else:
					#print 'adding ' + name + ' to unique list'
					self.unique_names[name] = ent
			self.ids[uid] = ent
			self.missing_entities.append(ent)
		return ent

def _entity_as_xml(registry, ent):
	is_unique = ent._name in registry._unique_names
	location_id = -1
	if(ent._vitals['location']):
		location_id = ent._vitals['location']._id	
	parent_id = -1
	if(ent._vitals['parent']):
		parent_id = ent._vitals['parent']._id	
	owner_id = -1
	if(ent._vitals['owner']):
		owner_id = ent._vitals['owner']._id
		
	result = entity_start % (ent._id, escape(ent._name), int(bool(is_unique)), ent._vitals['entity_type'], 
							parent_id, location_id, owner_id)
	
	result += _acl_as_xml(ent._vitals['acl'])
	
	unique_vals = []
	keys = ent._vdict.keys()
	keys.sort()
	for name in keys:
		attrib = ent._vdict[name]
		if(attrib not in unique_vals):
			if(isinstance(attrib, verb.Verb)):
				result += _verb_as_xml(name, attrib)
			elif(isinstance(attrib, prop.Property)):
				result += _property_as_xml(name, attrib)
			unique_vals.append(attrib)
	
	result += u'</Entity>'
	return result

def _acl_as_xml(acl):
	result = u'<ACL>'
	for item in acl:
		result += u' '.join(item)
		result += u"\n"
	result += u'</ACL>'
	return result

def _verb_as_xml(name, verb):
	owner_id = -1
	if(verb._vitals['owner']):
		owner_id = verb._vitals['owner']._id
	verb_names = verb.get_names(Q)
	primary_name = verb_names.pop(0)
	result = verb_start % (escape(primary_name), owner_id, int(bool(verb.is_ability(Q))), int(bool(verb.is_method(Q))))
	result += _acl_as_xml(verb._vitals['acl'])
	result += u'<Code>'
	result += escape(verb._vitals['code'])
	result += u'</Code>'
	for alias in verb_names:
		result += u"<Alias>%s</Alias>" % escape(alias)
	result += u'</Verb>'
	return result

def _property_as_xml(name, p):
	owner_id = -1
	if(p._vitals['owner']):
		owner_id = p._vitals['owner']._id
	result = prop_start % (escape(name), p.get_eval_type(Q), owner_id)
	result += _acl_as_xml(p._vitals['acl'])
	result += u'<Value>'
	if(p.get_eval_type(Q) == prop.EVAL_STRING):
		result += escape(p.get_value(Q))
	elif(p.get_eval_type(Q) in [prop.EVAL_DYNAMIC_CODE]):
		result += escape(p._vitals['code'])
	elif(p.get_eval_type(Q) == prop.EVAL_PYTHON):
		result += escape(repr(p.get_value(Q)))
	else:
		raise TypeError("Invalid property type: '%s'" % str(p.get_eval_type(Q)))
	result += u'</Value>'
	result += u'</Property>'
	return result

def escape(s):
	"""Replace special characters '&', "'", '<', '>' and '"' by XML entities."""
	if not(isinstance(s, basestring)):
		s = str(s)
	s = s.replace("&", "&amp;") # Must be done first!
	s = s.replace("'", "&apos;")
	s = s.replace("<", "&lt;")
	s = s.replace(">", "&gt;")
	s = s.replace('"', "&quot;")
	return s
	
def unescape(s):
	s = s.replace("&amp;", "&") # Must be done first!
	s = s.replace("&apos;", "'")
	s = s.replace("&lt;", "<")
	s = s.replace("&gt;", ">")
	s = s.replace('&quot;', '"')
	return s