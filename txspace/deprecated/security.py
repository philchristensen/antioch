# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Security


This module provides various security and permissions-related
functionality for the txSpace framework.
"""
from txspace import errors

# Q is a special marker used when executing protected
# functions from a system-level context. The choice was due
# to wanting a meaningless variable that evaulates to True.
Q = (None,)

group_registry = {}

def expose(func):
	func.exposed = True
	return func

@expose
def default_entity_acl(subject):
	allow(u'owners', u'anything', subject)
	allow(u'wizards', u'anything', subject)
	allow(u'everyone', u'get_children', subject)
	allow(u'everyone', u'get_contents', subject)
	allow(u'everyone', u'get_location', subject)
	allow(u'everyone', u'get_owner', subject)
	allow(u'everyone', u'get_parent', subject)
	allow(u'everyone', u'get_observations', subject)
	allow(u'everyone', u'get_observing', subject)
	allow(u'everyone', u'get_observers', subject)
	allow(u'everyone', u'observe', subject)
	allow(u'everyone', u'call_verb', subject)
	allow(u'everyone', u'get_verbs', subject)
	allow(u'everyone', u'get_verb_names', subject)
	allow(u'everyone', u'get_verb_info', subject)
	allow(u'everyone', u'get_callable_verb', subject)
	allow(u'everyone', u'get_property', subject)
	allow(u'everyone', u'get_properties', subject)
	allow(u'everyone', u'get_ancestor_with', subject)
	allow(u'everyone', u'write', subject)

@expose
def default_property_acl(subject):
	allow(u'owners', u'anything', subject)
	allow(u'wizards', u'anything', subject)

@expose
def readable_property_acl(subject):
	allow(u'owners', u'anything', subject)
	allow(u'wizards', u'anything', subject)
	allow(u'everyone', u'read', subject)

@expose
def default_verb_acl(subject):
	allow(u'owners', u'anything', subject)
	allow(u'wizards', u'anything', subject)
	allow(u'everyone', u'execute', subject)
	allow(u'everyone', u'read', subject)

def allow(accessor, access_str, subject):
	"""
	Allow an ability on this object. "obj" can be either a
	registered group name, or a object string (i.e., 
	#6 (wizard)). "access_str" is the ability descriptor string.
	"""
	acl = subject._vitals[u'acl']
	allow_permission = (u'allow', unicode(accessor), unicode(access_str))
	deny_permission = (u'deny', unicode(accessor), unicode(access_str))
	if(deny_permission in acl):
		acl.remove(deny_permission)
	if(allow_permission not in acl):
		acl.append(allow_permission)

def deny(accessor, access_str, subject):
	"""
	Remove an ability from this ACL. "object" can be either an
	Entity object or a Group object. "access_str" is the
	ability descriptor string.
	"""
	acl = subject._vitals[u'acl']
	allow_permission = (u'allow', unicode(accessor), unicode(access_str))
	deny_permission = (u'deny', unicode(accessor), unicode(access_str))
	if(allow_permission in acl):
		acl.remove(allow_permission)
	if(deny_permission not in acl):
		acl.append(deny_permission)

@expose
def is_allowed(accessor, access_str, subject):
	"""
	Does the given object have access? "object" can be either an
	Entity object or a Group object. "access_str" is the
	ability descriptor string.
	"""
	result = False
	if(accessor is Q):
		return True
	if(accessor is None):
		raise RuntimeError("Provided accessor was none.")
	for entry in subject._vitals[u'acl']:
		#if(access_str == u'set_observing'):
			#print u'checking u' + unicode(entry)
		if(entry[2] == access_str or entry[2] == u'anything'):
			#print "found accessor: " + entry[1]
			if(entry[1] == unicode(accessor)):
				# note that if something is explicitly denied,
				# we return immediately, so that some permissions
				# are excluded from u'anything'
				if(entry[0] == u'deny' and entry[2] != u'anything'):
					return False
				#print "a rule found: " + entry[0]
				result = (entry[0] == u'allow')
			elif(is_registered_group(entry[1]) and group_contains(entry[1], accessor, subject)):
				# see above
				if(entry[0] == u'deny' and entry[2] != u'anything'):
					return False
				#print "b rule found: " + entry[0]
				result = (entry[0] == u'allow')
	
	return result

def check_allowed(accessor, access_str, subject):
	if not(is_allowed(accessor, access_str, subject)):
		raise errors.ACLError(accessor, access_str, subject)

def is_registered_group(group_name):
	global group_registry
	return group_name in group_registry

def group_contains(group_name, accessor, subject):
	global group_registry
	return group_registry[group_name].contains(accessor, subject)

def register_group(group_name, group):
	global group_registry
	group_registry[group_name] = group

class Group(object):
	"""
	This class provides a way to categorize a number of users
	into a group. This is an abstract class. Implementations
	should use one of its subclasses, such as ListGroup or DynamicGroup
	"""	
	def __str__(self):
		module = unicode(self.__class__.__module__)
		if(module == "txspace.security"):
			module = unicode(self.__class__.__name__)
		else:
			module = module + "." + unicode(seld.__class__.__name__)
		return u"Group [%s]" % module
		
	def contains(self, accessor, subject):
		"""
		Is the given "object" part of this group?
		"""
		raise NotImplementedError, "contains(self, accessor, subject)"
	
class Owners(Group):
	"""
	By default, this group contains the owner of the
	given object, as well as any wizards.
	
	OBJ should own SOURCE
	"""
	def contains(self, accessor, subject):
		"""
		Is accessor the owner?
		"""
		#print unicode(subject)
		return subject._vitals[u'owner'] is accessor
		
class Everyone(Group):
	"""
	A special convenience group that includes everyone.
	"""
	def contains(self, accessor, subject):
		"""
		Always returns true.
		"""
		return True

class Wizards(Group):
	"""
	A group containing all wizards.
	"""
	def contains(self, accessor, subject):
		"""
		Returns true if obj is a wizard.
		"""
		return accessor.is_wizard(accessor)

class Programmers(Group):
	"""
	A group containing all programmers.
	"""
	def contains(self, accessor, subject):
		"""
		Returns true if obj is a programmer.
		"""
		return accessor.is_programmer(accessor)

class OwnerProgrammers(Group):
	"""
	Object is included if it is a programmer which
	owns the source object.
	"""
	def contains(self, accessor, subject):
		"""
		Returns true if obj is a programmer and owns the source.
		"""
		if not(accessor.is_programmer(accessor)):
			return False
		if not(subject.get_owner(accessor) is accessor):
			return False
		return True

class Self(Group):
	"""
	Object is included if it is the accessor or is defined on (or on a parent
	of) the accessor (we don't worry about whether the verb/property is readable
	or not, as that's what the ACL is for)
	"""
	def contains(self, accessor, subject):
		if(isinstance(subject, Entity)):
			return (subject == accessor)
		else:
			return (subject._vitals[u'origin'] == accessor or subject._vitals[u'origin'].has_child(accessor, accessor))

for group_class in (Owners, Everyone, Wizards, Programmers):
	group = group_class()
	register_group(group.__class__.__name__.lower(), group)
