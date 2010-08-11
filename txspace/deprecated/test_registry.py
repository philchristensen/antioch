# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

import unittest, string

from txspace import registry, entity, errors
from txspace.security import Q

class RegistryTestCase(unittest.TestCase):
	def setUp(self):
		self.registry = registry.Registry()
	
	def tearDown(self):
		self.registry = None
	
	def test_new(self):
		"""Check that new objects are created properly."""
		name = "New Object"
		next_id = len(self.registry._objects)
		obj = self.registry.new(name)
		self.assertEqual(obj.get_id(Q), next_id)
		self.assertEqual(self.registry._objects[next_id], obj)
		assert name.lower() in self.registry._names, 'new object not added to names db'
		self.assertRaises(errors.AmbiguousObjectError, self.registry.new, name, unique=True)
	
	def test_rename(self):
		"""Check that objects are renamed properly."""
		name = "New Object"
		new_name = "Renamed Object"
		obj = self.registry.new(name)
		self.registry.rename(obj, new_name)
		assert new_name.lower() in self.registry._names, 'renamed object not in names db'
		illegal_object = entity.Entity(self.registry, "Illegal Object")
		self.assertRaises(ValueError, self.registry.rename, illegal_object, new_name)
	
	def test_put(self):
		"""Check that pre-existing objects are added properly."""
		name = "New Object"
		obj = self.registry.new(name)
		obj_id = self.registry.put(obj)
		self.assertEqual(self.registry._objects[obj.get_id(Q)], obj)
		self.assertEqual(obj.get_id(Q), obj_id)
		assert name.lower() in self.registry._names, 'added object not in names db'
		assert obj in self.registry._names[name.lower()], 'added object not in names db'
		self.assertRaises(ValueError, self.registry.put, "a string")
		obj_id2 = self.registry.put(obj)
		self.assertEqual(obj_id, obj_id2)
	
	def test_get(self):
		"""Check that retreiving objects works properly."""
		name = "New Object"
		obj = self.registry.new(name)
		obj2 = self.registry.new(name)
		self.assertEqual(self.registry.get(obj.get_id(Q)), obj)
		self.assertEqual(self.registry.get(unicode(obj.get_id(Q))), obj)
		self.assertEqual(self.registry.get(str(obj)), obj)
		self.assertRaises(errors.AmbiguousObjectError, self.registry.get, name)
		self.assertRaises(errors.NoSuchObjectError, self.registry.get, "#fjkd")
		matches = self.registry.get(name, True)
		self.assertEqual(len(matches), 2)
		self.assertRaises(ValueError, self.registry.get, 420)
		self.registry.remove(matches[0])
		self.assertRaises(ValueError, self.registry.get, matches[0].get_id(Q))
		
	def test_refs(self):
		"""Check named reference counting."""
		name = "New Object"
		obj = self.registry.new(name)
		obj2 = self.registry.new(name)
		self.assertEqual(self.registry.refs(name), 2)
	
	def test_nothing(self):
		nothing = self.registry.get('#-1 (<<Unnamed>>)')
		self.assertEqual(nothing, None)
	
	def test_contains(self):
		"""Check registry containment testing."""
		name = "New Object"
		obj = self.registry.new(name)
		assert self.registry.contains(obj), 'contains does not return true'
	
	def test_remove(self):
		"""Check that object removal works properly."""
		name = "New Object"
		obj = self.registry.new(name)
		obj2 = self.registry.new(name)
		self.assertRaises(ValueError, self.registry.remove, "string")
		self.assertRaises(errors.NoSuchObjectError, self.registry.remove, 420)
		obj2.set_parent(Q, obj)
		self.assertRaises(errors.UserError, self.registry.remove, obj)
		self.registry.remove(obj2)
		self.assertEqual(self.registry.refs(name), 1)
		self.assertEqual(self.registry.size(), 2)
	
	def test_size(self):
		"""Check that registry.size() works properly."""
		name = "New Object"
		obj = self.registry.new(name)
		obj2 = self.registry.new(name)
		self.assertEqual(self.registry.size(), 3)

