# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

import unittest, string, sys, os, os.path

from txspace import registry, parser, errors, minimal
from txspace import auth, prop, security, assets
from txspace.security import Q

class FalseConnection:
	def get_type(self):
		return 'mock connection'
	def set_observations(self, *args, **kwargs):
		raise ClientObservationTestException(args)
	def write(self, *args, **kwargs):
		raise ClientWriteTestException(args)

class ClientObservationTestException(Exception):
	def __init__(self, data):
		self.data = data

class ClientWriteTestException(Exception):
	def __init__(self, data):
		self.data = data

class EntityTestCase(unittest.TestCase):
	def setUp(self):
		self.registry = registry.Registry()
		minimal.init(self.registry, assets.get_verbdir())
	
	def tearDown(self):
		self.registry = None
	
	def test_get_registry(self):
		sys = self.registry.get(0)
		obj = self.registry.new('obj');
		
		try:
			obj.get_registry(Q)
		except AttributeError:
			self.fail('obj.get_registry(Q) raised AttributeError')
		self.failUnlessRaises(AttributeError, obj.get_registry, sys)
		
	def test_set_connection(self):
		sys = self.registry.get(0)
		obj = self.registry.new('obj');
		
		try:
			obj.set_connection(Q, None)
		except AttributeError:
			self.fail('obj.set_connection(Q, None) raised AttributeError')
		self.failUnlessRaises(AttributeError, obj.set_connection, sys, None)
	
	def test_get_id(self):
		sys = self.registry.get(0)
		self.failUnlessEqual(sys.get_id(Q), 0)
	
	def test_get_name(self):
		room = self.registry.new("Test Room")
		self.failUnlessEqual(room.get_name(Q), 'Test Room')
		room.set_name(Q, 'Another Room')
		self.failUnlessEqual(room.get_name(Q), 'Another Room')
		self.failUnlessEqual(room.get_name(Q, real_name=True), 'Test Room')
	
	def test_set_name(self):
		room = self.registry.new("Test Room")
		room.set_name(Q, 'New Room')
		self.failUnlessEqual(room.get_name(Q), 'New Room')
		self.failUnlessEqual(room.get_name(Q, real_name=True), 'Test Room')
		
		room.set_name(Q, 'Another Room', real_name=True)
		self.failUnlessEqual(room.get_name(Q), 'New Room')
		self.failUnlessEqual(room.get_name(Q, real_name=True), 'Another Room')
	
	def test_has_child(self):
		parent = self.registry.new('parent');
		child = self.registry.new('child');
		child.set_parent(Q, parent)
		
		self.failUnless(parent.has_child(Q))
		self.failUnless(parent.has_child(Q, child))
	
	def test_get_children(self):
		parent = self.registry.new('parent');
		child = self.registry.new('child');
		child2 = self.registry.new('child2');
		child.set_parent(Q, parent)
		child2.set_parent(Q, parent)
		
		children = parent.get_children(Q)
		self.failUnless(child in children)
		self.failUnless(child2 in children)
	
	def test_has_parent(self):
		parent = self.registry.new('parent');
		child = self.registry.new('child');
		stranger = self.registry.new('stranger');
		child.set_parent(Q, parent)
		
		self.failIf(parent.has_parent(Q))
		self.failIf(child.has_parent(Q, stranger))
		self.failUnless(child.has_parent(Q))
		self.failUnless(child.has_parent(Q, parent))
		
	def test_get_parent(self):
		parent = self.registry.new('parent');
		child = self.registry.new('child');
		child.set_parent(Q, parent)
		self.failUnlessEqual(child.get_parent(Q), parent)
	
	def test_set_parent(self):
		parent = self.registry.new('parent');
		child = self.registry.new('child');
		grandchild = self.registry.new('grandchild');
		child.set_parent(Q, parent)
		grandchild.set_parent(Q, child)
		
		self.failUnless(child.has_parent(Q))
		self.failUnless(child.has_parent(Q, parent))
		self.failUnless(grandchild.has_parent(Q, parent))
		
		self.failUnless(child in parent.get_children(Q), "child not found in parent's children")
		self.failUnlessEqual(child.get_parent(Q), parent)
		self.assertRaises(errors.RecursiveError, parent.set_parent, Q, grandchild)
		self.assertRaises(TypeError, parent.set_parent, Q, 'some string')
		
		grandchild.set_parent(Q, None)
		child.set_parent(Q, grandchild)
		
		self.failIf(child in parent._vitals['children'], "child not removed from parent's children")
	
	def test_locations(self):
		room = self.registry.new('location test room');
		bucket = self.registry.new('bucket');
		brush = self.registry.new('brush');
		bucket.set_location(Q, room)
		brush.set_location(Q, bucket)
		
		self.failUnless(room.contains(Q, bucket))
		self.failUnless(room.contains(Q, brush))
		
		self.failUnlessEqual(room.find(Q, 'bucket'), bucket)
		
		pail = self.registry.new('bucket');
		pail.set_location(Q, room)
		
		brush.set_name(Q, 'A More Proper Brush')
		self.failUnlessEqual(bucket.find(Q, 'A More Proper Brush'), brush)
		
		brush.add_property(Q, 'aliases', ['brush alias'], owner=brush)
		self.failUnlessEqual(bucket.find(Q, 'brush alias'), brush)
		
		self.failUnlessRaises(errors.AmbiguousObjectError, room.find, Q, 'bucket')
		
		#self.failUnless(bucket in room._vitals['contents'], "object not found in location's contents")
		self.failUnless(bucket in room.get_contents(Q), "object not found in location's contents")
		#self.failUnless(bucket._vitals['location'] is room, "location not set on object")
		self.failUnless(bucket.get_location(Q) is room, "location not set on object")
		self.assertRaises(errors.RecursiveError, room.set_location, Q, brush)
		self.assertRaises(TypeError, room.set_location, Q, 'some string')
		
		brush.set_location(Q, None)
		bucket.set_location(Q, brush)
		
		self.failUnless(bucket not in room.get_contents(Q), "object not removed from location's children")
		
		room.add_verb(Q, 'return False', ['accept'], owner=self.registry.get('wizard'))
		self.failUnlessRaises(errors.PermissionError, brush.set_location, Q, room)
		self.failIfEqual(brush.get_location(Q), room)
		
		room._vdict['accept']._vitals['code'] = 'return True'
		del room._vdict['accept']._vitals['cache']
		brush.set_location(Q, room)
		
		bucket.set_location(Q, None)
		brush.set_location(Q, bucket)
		
		bucket.add_verb(Q, 'return False', ['provide'], owner=self.registry.get('wizard'))
		self.failUnlessRaises(errors.PermissionError, brush.set_location, Q, room)
		self.failIfEqual(brush.get_location(Q), None, room)
		
		bucket._vdict['provide']._vitals['code'] = 'return True'
		del bucket._vdict['provide']._vitals['cache']
		brush.set_location(Q, room)
		
		bucket.set_location(Q, None)
		brush.set_location(Q, bucket)
		
		room.add_verb(Q, 'raise UserError("")', ['enter'], owner=self.registry.get('wizard'))
		self.failUnlessRaises(errors.UserError, brush.set_location, Q, room)
		# failures in the 'enter' verb don't prevent location change,
		# but the observers can still be screwed up
		self.failUnlessEqual(brush.get_location(Q), room)
		
		bucket.set_location(Q, None)
		brush.set_location(Q, bucket)
		
		bucket.add_verb(Q, 'raise UserError("")', ['exit'], owner=self.registry.get('wizard'))
		self.failUnlessRaises(errors.UserError, brush.set_location, Q, room)
		self.failIfEqual(brush.get_location(Q), None)
	
	def test_observation(self):
		box = self.registry.new('box')
		guy = self.registry.new('guy')
		guy.set_player(Q)
		room = self.registry.new('observation test room')
		box.set_location(Q, room)
		guy.set_location(Q, room)
		
		guy._connection = FalseConnection()
		self.assertRaises(ClientObservationTestException, guy.set_observing, Q, room)
		
		self.failUnless(guy in room.get_observers(Q), "guy not found in room's observers")
		self.failUnlessEqual(guy.get_observing(Q), room, "guy not observing room")
		self.assertRaises(TypeError, guy.set_observing, Q, 'some string')
		
		self.assertRaises(ClientObservationTestException, guy.set_observing, Q, box)
		self.assertRaises(ClientObservationTestException, box.notify, Q)
		
		self.failUnless(guy not in room.get_observers(Q), "guy was still in room's observers")
		self.failUnless(guy in box.get_observers(Q), "guy not found in box's observers")
	
	def test_ownership(self):
		owner = self.registry.new('owner')
		posession = self.registry.new('posession')
		
		posession.set_owner(Q, owner)
		self.failUnlessEqual(posession.get_owner(Q), owner)
		#self.failUnlessEqual(posession._vitals['owner'], owner)
		self.failUnless(owner.owns(Q, posession))
	
	def test_observe(self):
		wizard = self.registry.get('wizard')
		classroom = self.registry.get('The Laboratory')
		wizard.set_location(Q, classroom)
		wizard._connection = FalseConnection()
		
		try:
			wizard.set_observing(Q, classroom)
		except ClientObservationTestException, e:
			self.failUnlessEqual(e.data[0]['name'], classroom.get_name(Q))
	
	def test_write(self):
		wizard = self.registry.get('wizard')
		classroom = self.registry.get('The Laboratory')
		wizard.set_location(Q, classroom)
		wizard._connection = FalseConnection()
		
		self.failUnlessRaises(ClientWriteTestException, wizard.write, Q, 'message')
	
	def test_verbs(self):
		wizard = self.registry.get('wizard')
		class_wizard = self.registry.get('class_wizard')
		
		self.failUnless(class_wizard.has_verb(Q, '@adduser'))
		self.failUnless(wizard.has_verb(Q, '@adduser', recurse=True))
		
		self.failUnless(class_wizard.has_callable_verb(Q, '@adduser'))
		self.failUnless(wizard.has_callable_verb(Q, '@adduser', recurse=True))
		
		wizard.add_verb(Q, 'raise UserError("")', ['test', 'test2'], owner=wizard)
		self.failUnlessRaises(errors.UserError, wizard.call_verb, Q, 'test')
		
		self.failUnless('test' in wizard.get_verbs(Q))
		self.failUnless('test2' in wizard.get_verb_names(Q, 'test'))
		wizard.set_verb_names(Q, 'test', ['test3', 'test4'])
		
		verb_names = wizard.get_verb_names(Q, 'test3')
		self.failUnless('test3' in verb_names)
		self.failUnless('test4' in verb_names)
		self.failUnless('test' not in verb_names)
		self.failUnless('test2' not in verb_names)
		
		wizard.remove_verb(Q, 'test3')
		self.failUnlessRaises(errors.NoSuchVerbError, wizard.get_verb_names, Q, 'test3')
		self.failUnlessRaises(errors.NoSuchVerbError, wizard.get_verb_names, Q, 'test4')
	
	def test_properties(self):
		wizard = self.registry.get('wizard')
		class_wizard = self.registry.get('class_wizard')
		
		self.failUnless(wizard.has_property(Q, 'passwd'))
		
		class_wizard.add_property(Q, 'test_prop', 'test value', owner=class_wizard)
		self.failIf(wizard.has_property(Q, 'test_prop', recurse=False))
		self.failUnless(wizard.has_property(Q, 'test_prop'))
		self.failUnlessEqual(class_wizard.get_property(Q, 'test_prop'), 'test value')
		
		self.failUnless(wizard.has_readable_property(Q, 'passwd'))
		self.failUnless('passwd' in wizard.get_properties(Q))
		
		class_wizard.set_property(Q, 'test_prop', 'new value')
		self.failUnlessEqual(class_wizard.get_property(Q, 'test_prop'), 'new value')
		
		class_wizard.remove_property(Q, 'test_prop')
		self.failIf('test_prop' in class_wizard.get_properties(Q))
	
	def test_player_state(self):
		wizard = self.registry.get('wizard')
		class_wizard = self.registry.get('class_wizard')
		
		self.failIf(class_wizard.is_player(Q))
		self.failUnless(wizard.is_player(Q))
		
		class_wizard.set_player(Q)
		self.failUnless(class_wizard.is_player(Q))
		
		wizard.set_connection(Q, FalseConnection())
		self.failUnless(wizard.is_connected_player(Q))
		
		wizard._connection = None
		self.failIf(class_wizard.is_connected_player(Q))
		
		self.failIf(class_wizard.is_programmer(Q))
		
		class_wizard.set_programmer(Q)
		self.failUnless(class_wizard.is_programmer(Q))
		
		class_wizard.set_wizard(Q)
		self.failUnless(class_wizard.is_wizard(Q))
		
		class_wizard.set_basic(Q)
		self.failIf(class_wizard.is_wizard(Q))
		self.failIf(class_wizard.is_programmer(Q))
		self.failIf(class_wizard.is_player(Q))

