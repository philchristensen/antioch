# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Registry


This class takes care of keeping references to all the objects in the
system, as well as sorting them by name. Whenever an object is requested
from the registry, if it is a non-unique name, Registry either returns a
list of matches, or throws a AmbiguousObjectError.

In naming objects, keep in mind that while multiple objects are allowed
with the same name, the registry is case-preserving, but case-insensitive.

This class also provides a mechanism for building "core" files, such as
the default minimal DB that would be distributed with txSpace.
Other starter cores could be used for different genres or platforms.

This should also make testing easier, as you can edit the external verb file
for version control purposes, but still have in-game code that's kept int
sync.
"""
from txspace import entity, errors
from txspace.security import Q

class Registry:
	"""
	The registry class is created by the service. One (and only one) instance
	exists at all times.
	"""
	def __init__(self, empty=False):
		""" Initialize the registry. """
		self._names = {}
		self._objects = []
		self._count = 0
		self._unique_names = []
		if not(empty):
			sys = self.new("System Object")
			sys.set_wizard(Q)
			
		self._verbs = {}
	
	def new(self, name, unique=False, ctx=Q):
		"""
		Create a new object with given name. If unique is True, then the name
		must be unique, or an AmbiguousObjectError will be thrown. If a unique
		object *is* created, all further calls to new(), put(), or rename() may
		not have that name.
		"""
		if(name in self._unique_names or (self.refs(name) > 0 and unique)):
			raise errors.AmbiguousObjectError(name, self.get(name, True, ctx=ctx), "You must specify a unique object name.")
		obj = entity.Entity(self, unicode(name))
		self.put(obj, ctx=ctx)
		if(unique):
			self._unique_names.append(name.lower())
		return obj
	
	def rename(self, obj, new_name, ctx=Q):
		"""
		Because of how objects are stored, this is the only way to change the
		name of an object (that is, the actual name. aliases and overridden names
		don't count).
		"""
		old_name = obj.get_name(ctx, real_name=True)
		if(old_name == new_name):
			return
		if(not self.contains(obj, ctx=ctx)):
			raise ValueError, "Invalid object."
		if(new_name.lower() in self._unique_names):
			raise errors.AmbiguousObjectError(new_name, self.get(new_name, True, ctx=ctx), "An object by that name already exists.")
		if(old_name.lower() in self._unique_names):
			self._unique_names.remove(old_name.lower())
			self._unique_names.append(new_name.lower())
		names = self._names[old_name.lower()]
		names.remove(obj)
		obj.__dict__['_name'] = new_name
		if(self.refs(new_name, ctx=ctx) > 0):
			self._names[new_name.lower()].append(obj)
		else:
			self._names[new_name.lower()] = [obj]
		obj.notify(ctx);
	
	def put(self, obj, unique=False, ctx=Q):
		"""
		Add a new object to the Registry. Normally, this method is only
		called internally, as verbs running in the restricted environment
		do not have access to the Entity class.
		"""
		if not(isinstance(obj, entity.Entity)):
			raise ValueError, "only Entity objects can be stored in the Registry."
		if(obj.get_name(ctx).lower() in self._unique_names):
			raise errors.AmbiguousObjectError(obj.get_name(ctx), self.get(name, ctx=ctx), "An object by that name already exists.")
		if(self.contains(obj, ctx=ctx)):
			return self._objects.index(obj)
		obj_name = obj.get_name(ctx, real_name=True)
		if(obj_name in self._unique_names or (self.refs(obj_name, ctx=ctx) > 0 and unique)):
			raise errors.AmbiguousObjectError(name, self.get(obj_name, True, ctx=ctx), "That object cannot be added as a unique name.")
		items = None
		if(unique):
			self._unique_names.append(obj_name.lower())
		if(self._names.has_key(obj_name.lower())):
			items = self._names[obj_name.lower()]
		else:
			items = []
			self._names[obj_name.lower()] = items
		items.append(obj)
		self._objects.append(obj)
		obj.__dict__['_id'] = self._objects.index(obj)
		self._count += 1
		return obj._id
	
	def get(self, key, return_list=False, ctx=Q):
		"""
		Retreive an object from the Registry. Either the name, id, or
		full string representation (i.e., "#1 (Wizard)") can be used as a key.
		"""
		#print 'requesting object by key: ' + repr(key)
		if(key == "None"):
			return None
		elif(key == ""):
			return None
		elif(key == '0' and self.size() == 0):
			# this helps when loading the xml
			# since we need to eval some stuff in an environment,
			# and get_environment always loads the system object
			return entity.Entity(self, 'Preload System Object')
		elif(isinstance(key, basestring)):
			#key = unicode(key)
			if(key.lower() in self._names):
				items = self._names[key.lower()]
				if(len(items) == 0):
					raise errors.NoSuchObjectError(key)
				elif(len(items) > 1):
					if(return_list):
						#WTF is this about, now?
						#i *think* this returns a copy
						return items * 1
					else:
						raise errors.AmbiguousObjectError(key, items)
				else:
					return items[0]
			else:
				try:
					if(key[0] == "#"):
						end = key.find("(")
						if(end == -1):
							end = key.find( " ")
						if(end == -1):
							end = len(key)
						return self.get(int(key[1:end]), ctx=ctx)
					else:
						return self.get(int(key), ctx=ctx)
				except ValueError, e:
					raise errors.NoSuchObjectError, key
		elif(isinstance(key, (int, long))):
			if(key == -1):
				return None
			if(key >= len(self._objects)):
				raise ValueError, "Invalid object ID"
			result = self._objects[key]
			if not(result):
				raise ValueError, "That object has been deleted."
			return result
		else:
			raise ValueError, "Invalid key type: " + repr(key)
	
	def refs(self, key, ctx=Q):
		"""
		How many objects in the store share the name given?
		"""
		if(key.lower() not in self._names):
			return 0
		else:
			return len(self._names[key.lower()]);
	
	def is_unique_name(self, key, ctx=Q):
	   return key in self._unique_names
	
	def contains(self, obj, ctx=Q):
		"""
		Has this object been added to the Registry? This method mostly only
		used internally.
		"""
		return obj in self._objects
	
	def remove(self, obj_id, ctx=Q):
		"""
		Remove an object from the Registry. If the object has children,
		they must be reassigned new parents, or deleted themselves, before
		the given object can be deleted. If the object contains other objects
		they are placed in the same location as the object to be removed.
		"""
		if(isinstance(obj_id, entity.Entity)):
			removed = obj_id
			obj_id = removed.get_id(ctx)
		elif not(isinstance(obj_id, int)):
			raise ValueError, "obj_id must be an Entity or an object id"
		else:
			if(obj_id < 0 or obj_id > len(self._objects) - 1):
				raise errors.NoSuchObjectError("Invalid ID")
			removed = self._objects[obj_id]
		if not(removed):
			return
		
		if(removed.get_children(ctx)):
			raise errors.UserError("That item cannot be deleted, as it has children.", removed)
		else:
			removed.set_parent(ctx, None)
		
		for item in removed.get_contents(ctx):
			item.set_location(removed.get_location(ctx))
		removed.set_location(ctx, None)
		
		self._count -= 1
		self._objects[obj_id] = None
		self._names[removed._name.lower()].remove(removed)
		if(removed._name.lower() in self._unique_names):
			self._unique_names.remove(removed._name.lower())
	
	def size(self, ctx=Q):
		"""
		Return the number of objects in the Registry.
		"""
		return self._count
	
	def load_verb(self, obj, verb_path, verb_names, ctx=Q, **kwargs):
		verb_info = [verb_names, verb_path, kwargs]
		for verb_name in verb_names:
			verb_key = str(obj.get_id(ctx)) + '-' + verb_name
			self._verbs[verb_key] = verb_info
		self._reload_verb(obj, verb_info)

	def reload_verb(self, obj, verb_name, ctx=Q):
		verb_key = str(obj.get_id(ctx)) + '-' + verb_name
		self._reload_verb(obj, self._verbs[verb_key])

	def _reload_verb(self, obj, verb_info, ctx=Q):
		verb_code = file(verb_info[1]).read()
		args = [verb_code, verb_info[0]]
		if(obj.has_verb(ctx, verb_info[0][0])):
			obj.remove_verb(ctx, verb_info[0][0])
		obj.add_verb(ctx, *args, **verb_info[2])
