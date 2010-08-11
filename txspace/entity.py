# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Entity


This module contains our primary object class (that is, for objects in the
system that can be directly manipulated by a user). This module is likely
to change vastly in the near future, as it has become an unweildy behemoth
that needs to be refactored. Hopefully, however, the interface will not change.
"""

import copy

from txspace import auth, errors, security, verb, prop
from txspace.security import Q

TYPE_BASIC = 0
TYPE_PLAYER = 1
TYPE_PROGRAMMER = 2
TYPE_WIZARD = 3

class Entity:
	"""
	This is the single object class for the entire "universe". All objects
	that can be directly manipulated by the user are instances of this class.
	As this class is meant to be wrapped by a Bastion-like object, properties
	and methods that need to be protected should be prefixed with a underscore.
	"""
		
	def __init__(self, registry, name):
		"""
		Create a new entity with the specified name.
		"""
		self._vitals = {u'entity_type':0,
						u'parent':None, u'children':[],
						u'location':None, u'contents':[],
						u'observing':None, u'observers':[],
						u'owner':self, u'acl':[]}
		self._vdict = {}
		self._name = name
		self._id = -1
		self._registry = registry
		security.default_entity_acl(self)
	
	def __str__(self):
		"""
		Return a string representation of this class. These take the form
		of "#0 (System Object)"; the object ID is prefixed by a pound sign,
		and the ID is followed by the real name of the object in parentheses.
		This string is suitable for handing to registry.get().
		"""
		idstr = "-1"
		name = "<<Unnamed>>"
		idstr = str(self._id)
		if(self._name):
			name = self._name
		return "#" + idstr + " (" + name + ")"
	
	def __unicode__(self):
		return unicode(str(self))
	
	def __repr__(self):
		"""
		Return the string representation of this object in the ususal
		repr fashion, wrapped in angle brackets. This is not currently
		supported by the registry.get() method.
		"""
		return "get_obj('" + str(self) + "')"
	
	def __add__(self, other):
		"""
		Treat this as a string when added to things.
		"""
		return str(self) + other
	
	def __radd__(self, other):
		"""
		Treat this as a string when added to things.
		"""
		return other + str(self)
	
	def __getstate__(self):
		"""
		When this gets saved to disk, we get rid of
		the client reference.
		"""
		state = self.__dict__.copy()
		if(state.has_key('_connection')):
			del state['_connection']
		return state
	
	def __setstate__(self, state):
		"""
		See __getstate__
		"""
		for key in state.keys():
			self.__dict__[key] = state[key]
	
	def get_registry(self, ctx):
		if(ctx is not Q):
			raise AttributeError('get_registry')
		return self._registry
	
	def set_connection(self, ctx, connection):
		if(ctx is not Q):
			raise AttributeError('set_connection')
		self._connection = connection
	
	def get_id(self, ctx):
		"""
		Return a unique ID for this object. This ID will never
		change or be recycled.
		"""
		return self._id
	
	def get_name(self, ctx, real_name=False):
		"""
		Return my name. If "real_name" is False, will return a property
		called "name", which may be different.
		"""
		if((not real_name) and self.has_property(ctx, "name")):
			return self.get_property(ctx, "name")
		return self._name
	
	def set_name(self, ctx, value, real_name=False):
		"""
		Change my real name
		"""
		security.check_allowed(ctx, 'set_name', self)
		if(real_name):
			self.get_registry(Q).rename(self, value)
		else:
			if(self.has_property(ctx, 'name')):
				self.set_property(ctx, 'name', value)
			else:
				self.add_property(ctx, 'name', value, owner=ctx)
	
	
	def has_child(self, ctx, obj=None):
		"""
		Is "obj" one of my children? Note that this returns True if any
		of my descendants have "obj" as a child.
		"""
		if(obj is None):
			return bool(self._vitals['children'])
		if(not isinstance(obj, Entity)):
			raise TypeError, "Invalid object: " + obj
		children = self.get_children(ctx)
		if(obj in children):
			return True
		elif(children):
			for child in children:
				if(child.has_child(ctx, obj)):
					return True
		return False
	
	def get_children(self, ctx):
		"""
		Return a list of objects that are my children. Note
		that modifying the returned list does not modify this instance.
		"""
		security.check_allowed(ctx, 'get_children', self)
		return copy.copy(self._vitals['children'])
	
	
	def has_parent(self, ctx, parent=None):
		"""
		Do I have a parent?
		"""
		if(parent is None):
			return self._vitals['parent'] != None
		else:
			return parent.has_child(ctx, self)
	
	def get_parent(self, ctx):
		"""
		Who do I inherit properties and verbs from?
		"""
		security.check_allowed(ctx, 'get_parent', self)
		return self._vitals['parent']
	
	def set_parent(self, ctx, new_parent):
		"""
		Set a new parent that this object will inherit properties and verbs from.
		"""
		security.check_allowed(ctx, 'set_parent', self)
		old_parent = self.get_parent(ctx)
		if(old_parent == new_parent):
			return
		#oh yeah, it happens....
		if(new_parent == self):
			raise errors.RecursiveError("An object cannot be parent to itself.")
		if(new_parent != None):
			if(not isinstance(new_parent, Entity)):
				raise TypeError, "Invalid object %r" % new_parent
			if(not security.is_allowed(ctx, 'add_child', new_parent)):
				raise errors.PermissionError, "Specified parent is not fertile."
			elif(self.has_child(ctx, new_parent)):
				raise errors.RecursiveError, ("%s is already a parent of %s" % (str(self), str(new_parent)))
		if(old_parent):
			old_parent._vitals['children'].remove(self)
		self._vitals['parent'] = new_parent
		if(new_parent):
			new_parent._vitals['children'].append(self)
	
	
	def find(self, ctx, name):
		"""
		Find an item named "name" in my contents. This method
		does not recurse.
		"""
		if(not name):
			return None
		matches = []
		for item in self.get_contents(ctx):
			if(item._name.lower() == name.lower()):
				matches.append(item)
				continue
			if(item.has_property(ctx, 'name') and item.get_property(ctx, 'name').lower() == name.lower()):
				matches.append(item)
				continue
			if(item.has_property(ctx, 'aliases')):
				alias_matches = []
				for alias in item.get_property(ctx, 'aliases'):
					if(alias.lower() == name.lower()):
						alias_matches.append(item)
				if(alias_matches):
					matches.extend(alias_matches)
					continue
		if(len(matches) > 1):
			raise errors.AmbiguousObjectError(name, matches)
		elif(not matches):
			return None
		return matches[0]
	
	def contains(self, ctx, obj):
		"""
		Does this object contain "obj", either directly or indirectly?
		"""
		if(not isinstance(obj, Entity)):
			raise TypeError, "Invalid object: " + obj
		contents = self.get_contents(ctx)
		if(obj in contents):
			return True
		elif(contents):
			for item in self.get_contents(ctx):
				if(item.contains(ctx, obj)):
					return True
		return False
	
	def get_contents(self, ctx):
		"""
		Return a list of objects that are contained in me. Note
		that modifying the returned list does not modify this instance.
		"""
		security.check_allowed(ctx, 'get_contents', self)
		return copy.copy(self._vitals['contents'])
	
	
	def get_location(self, ctx):
		"""
		Where am I?
		"""
		security.check_allowed(ctx, 'get_location', self)
		return self._vitals['location']
	
	def set_location(self, ctx, new_location):
		"""Move me to another location. Only the my owner or a wizard
		may do this. If a verb named "accept" exists on the new_location, it is
		called and passed this object as an argument. If it returns false, this
		object is not moved. If a verb named "provide" exists on the old_location, it is
		called and passed this object as an argument. If it returns false, this
		object is not moved.
		If I am moved, I will attempt to call a verb named
		"exit" on my old location before I move. I will also attempt to call a
		verb named "enter" on my new location after I move. Observers looking at
		me will be changed to be looking at the room, and I will begin observing
		my new location.
		"""
		security.check_allowed(ctx, 'set_location', self)
		old_location = self.get_location(ctx)
		#if we aren't going anywhere, don't do anything
		if(old_location == new_location):
			return
		#oh yeah, it happens....
		if(new_location == self):
			raise errors.RecursiveError("An object cannot be placed inside itself.")
		if(new_location):
			if(not isinstance(new_location, Entity)):
				raise TypeError, "Invalid object %r" % new_location
			elif(self.contains(ctx, new_location)):
				raise errors.RecursiveError("%s already contains %s" % (str(self), str(new_location)))
			elif(new_location.has_callable_verb(ctx, 'accept') and (not new_location.call_verb(ctx, 'accept', self))):
				raise errors.PermissionError("%s does not accept %s" % (str(new_location), str(self)))
		#call verbs "provide" and "exit" on the old location, if applicable
		if(old_location):
			if(old_location.has_callable_verb(ctx, 'provide') and (not old_location.call_verb(ctx, 'provide', self))):
				raise errors.PermissionError("%s will not provide %s" % (str(old_location), str(self)))
			if(old_location.has_callable_verb(ctx, 'exit')):
				old_location.call_verb(ctx, 'exit', self)
			#remove me from the content list for the old location
			old_location._vitals['contents'].remove(self)
			#this is okay, because self.location no longer 'remembers' self
			old_location.notify(ctx)
		
		#change observers
		#TODO: this does not affect observers who are looking at an item
		#   contained by this object.
		for observer in self.get_observers(ctx):
			observer_location = observer.get_location(ctx)
			if(observer_location != new_location):
				observer.set_observing(ctx, observer_location)
		
		#do the actual change
		self._vitals['location'] = new_location
		#call a verb "enter" on the new location, if applicable
		if(new_location):
			new_location._vitals['contents'].append(self)
			if(new_location.has_callable_verb(ctx, 'enter')):
				new_location.call_verb(ctx, 'enter', self)
			new_location.notify(ctx)
		#change what I am looking at.
		if(self.is_player(ctx)):
			self.set_observing(ctx, new_location)
	
	
	def owns(self, ctx, obj, slot_name=None):
		"""
		Do I own another object? If no owner was set for the "obj"
		argument, then return True. If slot_name is provided, report
		ownership of verb or property with that name
		"""
		if(slot_name):
			obj = obj._vdict[slot_name]
		if(obj is None):
			return False
		owner = obj.get_owner(ctx)
		if(owner == None):
			return True
		return self == owner
	
	def get_owner(self, ctx):
		"""
		Who owns me?
		"""
		security.check_allowed(ctx, 'get_owner', self)
		return self._vitals['owner']
	
	def set_owner(self, ctx, owner):
		"set owner to 'owner'"
		security.check_allowed(ctx, 'set_owner', self)
		self._vitals['owner'] =  owner
		return None
	
	
	def get_observers(self, ctx):
		"""
		Return a list of objects that are looking at me. Note
		that modifying the returned list does not modify this instance.
		"""
		security.check_allowed(ctx, 'get_observers', self)
		return copy.copy(self._vitals['observers'])
	
	def get_observations(self, ctx, system_object, client_code):
		"""
		This method returns an object that is serialized and returned
		to the client as part of the observation mechanism. First we
		attempt to call a verb "get_observations" on this entity, returning
		the result. If no such verb exists, or raises an exception, we
		attempt to call a verb with the same name on the System Object (#0),
		providing it with the object to get observations for, and a string
		that is a client code for the type of client connected.
		"""
		if(self.has_callable_verb(ctx, "get_observations")):
			return self.call_verb(ctx, "get_observations", client_code)
		elif(system_object.has_callable_verb(ctx, "get_observations")):
			return system_object.call_verb(ctx, "get_observations", self, client_code)
		return None
	
	def set_observing(self, ctx, new_observing):
		"""
		Change the object I am observing to "new_observing".
		"""
		security.check_allowed(ctx, 'set_observing', self )
		old_observing = self.get_observing(ctx)
		if not(self.is_connected_player(ctx)):
			return
		# after much thought, this is being left out
		# so we have a way to force the client to
		# refresh its view	
		#if(old_observing == new_observing):
		#	return
		if(new_observing):
			if(not isinstance(new_observing, Entity)):
				raise TypeError, "Invalid object %r" % new_observing
		if(old_observing):
			old_observing._vitals['observers'].remove(self)
		self._vitals['observing'] = new_observing
		if(new_observing):
			new_observing._vitals['observers'].append(self)
		self.observe(ctx, new_observing)
	
	def get_observing(self, ctx):
		"""
		What am I looking at?
		"""
		security.check_allowed(ctx, 'get_observing', self)
		return self._vitals['observing']
	
	def observe(self, ctx, obj):
		"""
		Update my client vis-a-vis my observations.
		"""
		security.check_allowed(ctx, 'observe', self)
		if not(self.is_player(ctx)):
			raise errors.PermissionError, "A non-player entity cannot be observe something!"
		if(self.is_connected_player(ctx)):
			if(obj is None):
				observations = {u'name':'Nothingness',u'description':u"There's not a whole lot to see here.", u'contents':[]}
				self._connection.set_observations(observations)
			else:
				system_object = self.get_registry(Q).get(0)
				observations = obj.get_observations(ctx, system_object, self._connection.get_type())
				self._connection.set_observations(observations)
	
	def notify(self, ctx):
		"""
		Tell all of my observers to refresh their view of me.
		"""
		for observer in self.get_observers(ctx):
			observer.observe(ctx, self)
		if(self.get_location(ctx)):
			self.get_location(ctx).notify(ctx)
	
	
	def get_details(self, ctx):
		"""
		An interface for gaining programmatic info about an object.
		"""
		
		details = {u'name':unicode(self.get_name(ctx, True)), u'id':self.get_id(ctx),
				   u'parent':unicode(self.get_parent(ctx)), u'location':unicode(self.get_location(ctx)),
				   u'owner':unicode(self.get_owner(ctx))}
		
		contents = self.get_contents(ctx)
		children = self.get_children(ctx)
		properties = self.get_properties(ctx)
		verbs = self.get_verbs(ctx)
		for array in [children, contents, properties, verbs]:
			for i in range(len(array)):
				array[i] = unicode(array[i])
		details[u'children'] = children
		details[u'contents'] = contents
		details[u'properties'] = properties
		details[u'verbs'] = verbs
		details[u'entity_type'] = self._vitals['entity_type']
		details[u'acl'] = copy.copy(self._vitals['acl'])
		return details
	
	def set_details(self, ctx, info):
		"""
		Set all internal entity attributes at once.
		"""
		self.set_name(ctx, info[u'name'], real_name=True)
		self.set_parent(ctx, self._registry.get(info[u'parent']))
		self.set_location(ctx, self._registry.get(info[u'location']))
		self.set_owner(ctx, self._registry.get(info[u'owner']))
		self._vitals[u'entity_type'] = info[u'entity_type']
	
	def write(self, ctx, text, is_error=False):
		"""
		Write a line of text to my client.
		"""
		security.check_allowed(ctx, 'write', self)
		if not(self.is_connected_player(ctx)):
			raise errors.PermissionError, "A non-connected-player entity cannot be written to!"
		if(hasattr(self, '_connection')):
			self._connection.write(text, is_error=is_error)
	
	def get_ancestor_with(self, ctx, name):
		"""
		Return the object in this object's "family tree" that provides
		the verb or property named "name"
		"""
		security.check_allowed(ctx, 'get_ancestor_with', self)
		if(self._vdict.has_key(name)):
			return self
		else:
			parent = self.get_parent(ctx)
			if(parent):
				return parent.get_ancestor_with(ctx, name)
			else:
				return None
	
	
	def has_verb(self, ctx, name, recurse=True):
		"""
		Do I (or, optionally, any of my parents) support the verb "name"?
		"""
		if(recurse):
			found = self.get_ancestor_with(ctx, name)
			if(not found):
				return False
		else:
			found = self
		if(name not in found._vdict):
			return False
		v = found._vdict[name]
		if(not isinstance(v, verb.Verb)):
			return False
		return True
	
	def has_callable_verb(self, ctx, name, recurse=True):
		"""
		This function should only return true if it's possible for
		the current user to execute the verb. Right now, it has
		the same functionality as has_verb.
		"""
		#TODO: make this work properly
		return self.has_verb(ctx, name, recurse=recurse)
	
	def call_verb(self, ctx, name, *args, **kwargs):
		"""
		Call a verb programmatically, and return the result. It is yet to be
		decided how the verb will return a result.
		"""
		security.check_allowed(ctx, 'call_verb', self)
		if not(self.has_verb(ctx, name)):
			raise AttributeError, "There is no verb by the name '%s' on %s." % (name, str(self))
		ancestor = self.get_ancestor_with(ctx, name)
		return ancestor._vdict[name].call(ctx, self, args, kwargs)
	
	def get_verbs(self, ctx):
		"""
		Return a list of the names of all the verbs I implement.
		"""
		security.check_allowed(ctx, 'get_verbs', self)
		verbs = []
		for name in self.__dict__['_vdict']:
			item = self.__dict__['_vdict'][name]
			if(isinstance(item, verb.Verb)):
				verbs.append(name)
		verbs.sort()
		return verbs
	
	def get_verb_names(self, ctx, name):
		"""
		Get a list of other names for the verb, "name".
		"""
		security.check_allowed(ctx, 'get_verb_names', self)
		if(not self.has_verb(ctx, name)):
			raise errors.NoSuchVerbError, ("There is no verb '%s' on %s" % (name, str(self)))
		elif(not self._vdict[name].is_readable(ctx)):
			raise errors.PermissionError, ("verb.Verb '%s' is not publicly readable." % name)
		return self._vdict[name].get_names(ctx)
	
	def set_verb_names(self, ctx, name, names):
		"""
		Set the list of names for the verb, "name".
		"""
		security.check_allowed(ctx, 'set_verb_names', self)
		if(not self.has_verb(ctx, name)):
			raise errors.NoSuchverb.VerbError, ("There is no verb '%s' on %s" % (name, str(self)))
		elif(not self._vdict[name].is_writeable(ctx)):
			raise errors.PermissionError, ("verb.Verb '%s' is not publicly writeable." % name)
		for n in names:
			if(n in self._vdict and self._vdict[n] is self._vdict[name]):
				raise errors.PermissionError, ("There is already a verb named '%s' on %s" % (n, str(self)))
		v = self._vdict[name]
		self.remove_verb(ctx, name)
		v.set_names(ctx, names)
		for n in v.get_names(ctx):
			self._vdict[n] = v
	
	def add_verb(self, ctx, code, names, **kwargs):
		"""
		Add a new verb to this object. Note that if there is any verb or property
		with a name in the 'names', this verb is not added at all.
		"""
		security.check_allowed(ctx, 'add_verb', self)
		for name in names:
			if(self.has_property(ctx, name, 0)):
				raise AttributeError, ("There is already a property by the name '%s' on the entity %s" % (name, str(self)))
			if(self.has_verb(ctx, name, 0)):
				raise AttributeError, ("There is already a verb by the name '%s' on the entity %s" % (name, str(self)))
		
		v = verb.Verb(ctx, code, names, origin=self, **kwargs)
		for name in names:
			self._vdict[name] = v
	
	def remove_verb(self, ctx, name):
		"""
		Removes a verb from this object.
		"""
		security.check_allowed(ctx, 'remove_verb', self)
		v = self._vdict[name]
		for n in v.get_names(ctx):
			if(self._vdict[n] == v):
				del self._vdict[n]
	
	
	def has_property(self, ctx, name, recurse=True):
		"""
		Do I (or one of my ancestors) provide a property "name"?
		"""
		if(recurse):
			found = self.get_ancestor_with(ctx, name)
		if(not recurse):
			found = self
		if(not found):
			return False
		if(not found._vdict.has_key(name)):
			return False
		p = found._vdict[name]
		if(not isinstance(p, prop.Property)):
			return False
		if(found != self and (not p.is_inherited(ctx))):
			return False
		return True
	
	def has_readable_property(self, ctx, name, recurse=True):
		ancestor = self.get_ancestor_with(ctx, name)
		if not(ancestor):
			return False
		p = ancestor._vdict[name]
		if not(isinstance(p, prop.Property)):
			return False
		if(ancestor is not self and not recurse):
			return False
		return ancestor._vdict[name].is_readable(ctx)
	
	def get_property(self, ctx, name, recurse=True):
		"""
		Return the value of the property "name", optionally recursing through
		ancestors until it is found or there are no more ancestors.
		"""
		security.check_allowed(ctx, 'get_property', self)
		if(recurse):
			found = self.get_ancestor_with(ctx, name)
		if((not recurse) or (not found)):
			found = self
		if(not found.has_property(ctx, name, False)):
			raise AttributeError, ("The entity %s does not have a property '%s'" % (str(self), name))
		p = found._vdict[name]
		if(found != self and (not p.is_inherited(ctx))):
			raise errors.PermissionError, ("The property '%s' on %s is not inherited by %s." % (name, str(found), str(self)))
		if(p.is_readable(ctx)):
			return p.get_value(ctx)
		else:
			raise errors.PermissionError, ("The property '%s' on %s is not publicly readable." % (name, str(self)))
	
	def get_properties(self, ctx):
		"""
		Return a list of properties on this object.
		"""
		security.check_allowed(ctx, 'get_properties', self)
		props = []
		attribs = self._vdict.keys()
		for name in attribs:
			item = self._vdict[name]
			if(isinstance(item, prop.Property)):
				props.append(name)
		props.sort()
		return props
	
	def add_property(self, ctx, name, value, **kwargs):
		security.check_allowed(ctx, 'add_property', self)
		if(self.has_property(ctx, name)):
			raise AttributeError("There is already a property by the name '%s' on the entity %s" % (name, str(self)))
		if(self.has_property(ctx, name, False) and (not self._vdict[name].is_writeable())):
			raise errors.PermissionError("The property '%s' on %s is not writeable." % (name, str(self)))
		
		self._vdict[name] = prop.Property(ctx, value, origin=self, **kwargs)
	
	def set_property(self, ctx, name, value):
		"""
		Add/set the value of a property on this object.
		"""
		security.check_allowed(ctx, 'set_property', self)
		if not(self.has_property(ctx, name, False)):
			if(self.has_property(ctx, name)):
				obj = self.get_ancestor_with(ctx, name)
				item = obj._vdict[name]
				if(item.is_inherited(ctx)):
					self._vdict[name] = item.clone(ctx, self)
				else:
					raise errors.PermissionError("The property '%s' defined on %s is not inherited." % (name, str(obj)))
			else:
				raise AttributeError("There is no property by the name '%s' on the entity %s. Use add_property first." % (name, str(self)))
		p = self._vdict[name]
		if(not p.is_writeable(ctx)):
			raise errors.PermissionError("The property '%s' on %s is not writeable." % (name, str(self)))
		else:
			p.set_value(ctx, value)
	
	def remove_property(self, ctx, name):
		security.check_allowed(ctx, 'remove_property', self)
		if not(self.has_property(ctx, name)):
			raise AttributeError, ("The entity %s does not have a property '%s'" % (str(self), name))
		del self._vdict[name]
	
	def get_entity_type(self, ctx):
		"""
		Get the type ID of this object.
		"""
		return self._vitals['entity_type']
	
	def set_basic(self, ctx):
		"""
		Set if this a regular object (used to 'unset' player/programmer/wizard status).
		"""
		security.check_allowed(ctx, 'set_basic', self)
		self._vitals['entity_type'] = TYPE_BASIC
	
	def set_player(self, ctx):
		"""
		Set if this a representation of a user. A user object needs this flag
		set, as well as a "passwd" property, to login.
		"""
		security.check_allowed(ctx, 'set_player', self)
		self._vitals['entity_type'] = TYPE_PLAYER
	
	def is_player(self, ctx):
		"""
		Is this a representation of a user?
		"""
		return self._vitals['entity_type'] >= TYPE_PLAYER
	
	def is_connected_player(self, ctx):
		if not(self.is_player(ctx)):
			return False
		if not(hasattr(self, "_connection")):
			return False
		if(self._connection is None):
			return False
		return True
	
	def set_programmer(self, ctx):
		"""
		Set if this player is a programmer.
		"""
		security.check_allowed(ctx, 'set_programmer', self)
		self._vitals['entity_type'] = TYPE_PROGRAMMER
	
	def is_programmer(self, ctx):
		"""
		Is this object's user a programmer?
		"""
		return self._vitals['entity_type'] >= TYPE_PROGRAMMER
	
	def set_wizard(self, ctx):
		"""
		Set if this player is a wizard.
		"""
		security.check_allowed(ctx, 'set_wizard', self)
		self._vitals['entity_type'] = TYPE_WIZARD
	
	def is_wizard(self, ctx):
		"""
		Is this object's user a wizard?
		"""
		return self._vitals['entity_type'] >= TYPE_WIZARD

