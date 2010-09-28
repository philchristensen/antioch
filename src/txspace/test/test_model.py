# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

from twisted.trial import unittest

from txspace import model, test, errors

class EntityTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_id(self):
		e = test.Anything()
		o = model.Object(e)
		o.set_id(1024)
		
		self.failUnlessEqual(o.get_id(), 1024)
		self.failUnlessEqual(o.id, 1024)
		self.failUnlessRaises(RuntimeError, o.set_id, 2048)
		
	def test_owner(self):
		e = test.Anything(
			instantiate	= lambda *a, **kw: owner,
			get_context	= lambda: None,
			save		= lambda s: True,
		)
		
		owner = model.Object(e)
		owner_mock = test.Anything(
			get_id	= lambda: 1024,
		)
		subject = model.Object(e)
		subject2 = model.Property(subject)
		subject3 = model.Verb(subject)
		
		subject.set_owner(owner_mock)
		self.failUnlessEqual(subject.get_owner(), owner)
		self.failUnlessEqual(subject.owner, owner)
		
		subject2.set_owner(owner_mock)
		self.failUnlessEqual(subject2.get_owner(), owner)
		self.failUnlessEqual(subject2.owner, owner)
		
		subject3.set_owner(owner_mock)
		self.failUnlessEqual(subject3.get_owner(), owner)
		self.failUnlessEqual(subject3.owner, owner)
	
	def test_origin(self):
		e = test.Anything(
			instantiate	= lambda *a, **kw: origin,
			get_context	= lambda: None,
		)
		
		origin = model.Object(e)
		p = model.Property(origin)
		
		self.failUnlessEqual(p.get_origin(), origin)
		self.failUnlessEqual(p.origin, origin)
		
		v = model.Verb(origin)
		self.failUnlessEqual(v.get_origin(), origin)
		self.failUnlessEqual(v.origin, origin)
	
	def test_get_exchange(self):
		e = test.Anything()
		o = model.Object(e)
		self.failUnlessEqual(o.get_exchange(), e)
	
	def test_get_context(self):
		e = test.Anything(
			get_context	= lambda: o
		)
		o = model.Object(e)
		self.failUnlessEqual(o.get_context(), o)
	
	def test_get_obj_details(self):
		e = test.Anything(
			get_context			= lambda: None,
			save				= lambda x: None,
			is_unique_name		= lambda n: False,
			get_details			= lambda *a, **kw: self.failUnlessEqual((a,kw), ''),
			get_parents			= lambda i, r: [],
			get_verb_list		= lambda i: [],
			get_property_list	= lambda i: [],
		)
		o = model.Object(e)
		o.set_id(1024)
		o.set_name('test object', real=True)
		
		details = o.get_details()
		self.failUnlessEqual(details, dict(
			id			= 1024,
			kind		= 'object',
			location	= 'None',
			name		= 'test object',
			owner		= 'None',
			parents		= '',
			properties	= [],
			verbs		= [],
		))
	
	def test_get_verb_details(self):
		e = test.Anything(
			get_context			= lambda: None,
			# save				= lambda x: None,
			# is_unique_name		= lambda n: False,
			# get_details			= lambda *a, **kw: self.failUnlessEqual((a,kw), ''),
			get_parents			= lambda i, r: [],
			get_verb_list		= lambda i: [],
			get_property_list	= lambda i: [],
			get_verb_names		= lambda i: ['test'],
			add_verb_name		= lambda i, n: self.failUnlessEqual(n, 'test'),
			instantiate			= lambda *a, **kw: o if a[0] == 'object' else v,
		)
		o = model.Object(e)
		o.set_id(1024)
		v = model.Verb(o)
		v.set_names(['test'])
		
		details = v.get_details()
		self.failUnlessEqual(details, dict(
			id			= 0,
			kind		= 'verb',
			code		= '',
			exec_type	= 'verb',
			names		= ['test'],
			owner		= 'None',
			origin		= '#1024 ()',
		))
		
	def test_save(self):
		e = test.Anything(
			save = lambda x: test.raise_e(errors.TestError())
		)
		o = model.Object(e)
		self.failUnlessRaises(errors.TestError, o.save)
	
	def test_destroy(self):
		e = test.Anything(
			destroy		= lambda x: test.raise_e(errors.TestError()),
			get_context = lambda: None,
		)
		o = model.Object(e)
		self.failUnlessRaises(errors.TestError, o.destroy)

class ObjectTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_owns(self):
		e = test.Anything(
			get_context	= lambda: None,
			save		= lambda x: None,
			instantiate	= lambda *a, **kw: owner if kw['id'] == 1024 else subject,
		)
		owner = model.Object(e)
		owner.set_id(1024)
		subject = model.Object(e)
		subject.set_id(2048)
		subject.set_owner(owner)
		
		self.failUnlessEqual(owner.owns(subject), True)
	
	def test_verb(self):
		e = test.Anything(
			get_verb	= lambda *a, **kw: (a, kw),
			get_context	= lambda: o,
			is_allowed	= lambda *a: True,
		)
		o = model.Object(e)
		
		self.failUnlessEqual(getattr(o, 'look'), ((0, 'look',), {'recurse':True}))
		self.failUnlessEqual(o.get_verb('look', recurse=False), ((0, 'look',), {'recurse':False}))
	
	def test_add_verb(self):
		class _VerbAdded(Exception):
			pass
		
		def _err(name):
			raise _VerbAdded(name)
		
		v = test.Anything(
			add_name	= lambda name: _err(name),
		)
		x = test.Anything(
			get_id		= lambda: -1,
		)
		e = test.Anything(
			instantiate	= lambda *a, **kw: v,
			get_context	= lambda: o,
			ctx			= x,
			is_allowed	= lambda *a: True,
		)
		o = model.Object(e)
		
		self.failUnlessRaises(_VerbAdded, o.add_verb, 'look')
	
	def test_has_verb(self):
		e = test.Anything(
			has		=	lambda *a, **kw: (a, kw),
		)
		o = model.Object(e)
		o.set_id(1024)
		v = test.Anything(
		)
		
		self.failUnlessEqual(o.has_verb('look'), ((1024, 'verb', 'look'), {}))
		self.failUnlessEqual(o.has_callable_verb('look'), ((1024, 'verb', 'look'), {'unrestricted': False}))
	
	def test_remove_verb(self):
		e = test.Anything(
			get_context		= lambda: None,
			remove_verb		= lambda *a, **kw: self.failUnlessEqual(kw, {'name': 'test', 'origin_id': 1024})
		)
		o = model.Object(e)
		o.set_id(1024)
		
		o.remove_verb('test')
	
	def test_get_property(self):
		e = test.Anything(
			get_property	= lambda *a, **kw: p,
			get_context		= lambda: o,
			is_allowed		= lambda *a: True,
		)
		o = model.Object(e)
		p = test.Anything(
			origin		= lambda: o,
			get_type	= lambda: 'string',
			get_id		= lambda: -1,
		)
		
		self.failUnlessEqual(o['description'], p)
		self.failUnlessEqual(o.get_property('description'), p)
	
	def test_add_property(self):
		class _PropertyAdded(Exception):
			pass
		
		def _err(name):
			raise _PropertyAdded(name)
		
		x = test.Anything(
			get_id		= lambda: -1
		)
		e = test.Anything(
			instantiate	= lambda *a, **kw: (a, kw),
			get_context	= lambda: o,
			is_allowed	= lambda *a: True,
		)
		o = model.Object(e)
		o.set_id(1024)
		p = test.Anything(
			origin	= lambda: o
		)
		
		self.failUnlessEqual(o.add_property('description'), (('property',), dict(name='description',origin_id=1024,owner_id=1024)))
	
	def test_has_property(self):
		e = test.Anything(
			has		=	lambda *a, **kw: (a, kw),
		)
		o = model.Object(e)
		o.set_id(1024)
		v = test.Anything(
		)
		
		self.failUnlessEqual('description' in o, True)
		self.failUnlessEqual(o.has_property('description'), ((1024, 'property', 'description'), {}))
		self.failUnlessEqual(o.has_readable_property('description'), ((1024, 'property', 'description'), {'unrestricted': False}))
	
	def test_remove_property(self):
		e = test.Anything(
			get_context		= lambda: None,
			remove_property	= lambda **kw: self.failUnlessEqual(kw, {'name': 'test', 'origin_id': 1024})
		)
		o = model.Object(e)
		o.set_id(1024)
		
		o.remove_property('test')
	
	def test_get_ancestor_with(self):
		e = test.Anything(
			get_context		= lambda: None,
			get_ancestor_with	= lambda *a: self.failUnlessEqual(a, (1024, 'verb', 'test'))
		)
		o = model.Object(e)
		o.set_id(1024)
		
		o.get_ancestor_with('verb', 'test')
	
	def test_is_player(self):
		e = test.Anything(
			is_player	=	lambda *a, **kw: (a, kw),
		)
		o = model.Object(e)
		o.set_id(1024)
		
		self.failUnlessEqual(o.is_player(),  ((1024,), {}))
	
	def test_is_connected_player(self):
		e = test.Anything(
			get_context		= lambda: None,
			is_connected_player	= lambda *a, **kw: self.failUnlessEqual(a[0], 1024)
		)
		o = model.Object(e)
		o.set_id(1024)
		
		o.is_connected_player()
	
	def test_set_player(self):
		e = test.Anything(
			get_context		= lambda: None,
			set_player	= lambda *a, **kw: self.failUnlessEqual(a, (1024, True, True, 'passwd'))
		)
		o = model.Object(e)
		o.set_id(1024)
		
		o.set_player(True, True, 'passwd')
	
	def test_name(self):
		uniques = [False, True]
		hases = [True, True, False, False, False]
		e = test.Anything(
			is_unique_name		= lambda name: uniques.pop(),
			has					= lambda *a, **kw: hases.pop(),
			instantiate			= lambda *a, **kw: p,
			get_property		= lambda *a, **kw: p,
			get_context			= lambda: o,
			is_allowed			= lambda *a: True,
			save				= lambda s: True,
		)
		e.ctx = test.Anything(
			get_id				=	lambda: -1
		)
		
		o = model.Object(e)
		p = model.Property(o)
		
		self.failUnlessRaises(ValueError, o.set_name, 'phil', real=True)
		o.set_name('phil', real=True)
		
		#import pdb; pdb.set_trace()
		self.failUnlessEqual(o.get_name(), 'phil')
		self.failUnlessEqual(o.name, 'phil')
		
		o.set_name('phil-prop')
		
		self.failUnlessEqual(o.get_name(real=True), 'phil')
		self.failUnlessEqual(o.get_name(), 'phil-prop')
		self.failUnlessEqual(o.name, 'phil-prop')
		
	
	def test_location(self):
		contained = [False, True]
		e = test.Anything(
			instantiate	= lambda *a, **kw: room,
			contains	= lambda *a, **kw: contained.pop(),
			get_context	= lambda: subject,
			is_allowed	= lambda *a: True,
			save		= lambda s: True,
		)
		room = model.Object(e)
		room_mock = test.Anything(
			get_id	= lambda: 1024,
			has_verb = lambda v: None,
		)
		subject = model.Object(e)
		
		self.failUnlessRaises(errors.RecursiveError, subject.set_location, room_mock)
		
		subject.set_location(room_mock)
		self.failUnlessEqual(subject.get_location(), room)
		self.failUnlessEqual(subject.location, room)
	
	def test_find(self):
		e = test.Anything(
			get_context		= lambda: None,
			find			= lambda *a: self.failUnlessEqual(a, (1024, 'thing'))
		)
		container = model.Object(e)
		container.set_id(1024)
		
		container.find('thing')
	
	def test_contains(self):
		e = test.Anything(
			get_context		= lambda: None,
			contains		= lambda *a: self.failUnlessEqual(a, (1024, 2048, True))
		)
		container = model.Object(e)
		container.set_id(1024)
		thing = model.Object(e)
		thing.set_id(2048)
		
		container.contains(thing)
	
	def test_get_contents(self):
		e = test.Anything(
			get_context		= lambda: None,
			get_contents	= lambda *a: self.failUnlessEqual(a[0], 1024)
		)
		container = model.Object(e)
		container.set_id(1024)
		
		container.get_contents()
	
	def test_parent(self):
		e = test.Anything(
			add_parent	= lambda *a, **kw: (a, kw),
			get_parents = lambda *a, **kw: [parent],
			has_parent	= lambda p, r: True,
			get_context	= lambda: child,
			is_allowed	= lambda *a: True,
		)
		child = model.Object(e)
		child.set_id(1024)
		
		child_mock = test.Anything(
			has_parent	= lambda p: True,
			get_id		= lambda: parent.get_id(),
		)
		
		parent = model.Object(e)
		parent.set_id(2048)
		
		parent_mock = test.Anything(
			has_parent	= lambda p: False,
			get_id		= lambda: parent.get_id(),
			get_type	= lambda: 'object',
		)
		
		child.add_parent(parent_mock)
		self.failUnlessRaises(errors.RecursiveError, parent.add_parent, child)
		self.failUnlessEqual(child.get_parents(), [parent])
	
	def test_remove_parent(self):
		e = test.Anything(
			get_context		= lambda: None,
			remove_parent	= lambda *a: self.failUnlessEqual(a, (2048, 1024))
		)
		child = model.Object(e)
		child.set_id(1024)
		parent = model.Object(e)
		parent.set_id(2048)
		
		child.remove_parent(parent)
	
	def test_check(self):
		allowances = [True, False]
		e = test.Anything(
			is_allowed	= lambda *a: allowances.pop(),
			get_context	= lambda: ctx,
		)
		ctx = model.Object(e)
		
		person = model.Object(e)
		item = model.Object(e)
		
		self.failUnlessRaises(errors.PermissionError, person.check, 'move', item)
		self.failUnlessEqual(person.is_allowed('move', item), True)
	

class VerbTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_id(self):
		e = test.Anything()
		o = model.Object(e)
		v = model.Verb(o)
		v.set_id(1024)
		
		self.failUnlessEqual(v.get_id(), 1024)
		self.failUnlessRaises(RuntimeError, v.set_id, 2048)
	
	def test_origin(self):
		e = test.Anything(
			instantiate	= lambda *a, **kw: (a, kw),
			is_allowed	= lambda *a: True,
			get_context	= lambda: o,
		)
		o = model.Object(e)
		o.set_id(1024)
		v = model.Verb(o)
		
		self.failUnlessEqual(v.get_origin(), (('object',), {'id': 1024}))
	
	def test_names(self):
		e = test.Anything(
			get_verb_names	= lambda *a, **kw: (a, kw),
		)
		o = model.Object(e)
		v = model.Verb(o)
		v.set_id(2048)
		
		self.failUnlessEqual(v.get_names(), ((2048,), {}))
	
	def test_set_names(self):
		e = test.Anything(
			get_context		= lambda: None,
			get_verb_names	= lambda i: [],
			add_verb_name	= lambda *a: self.failUnlessEqual(a, (2048, 'test'))
		)
		o = model.Object(e)
		o.set_id(1024)
		v = model.Verb(o)
		v.set_id(2048)
		
		v.set_names(['test'])
	
	def test_add_name(self):
		e = test.Anything(
			add_verb_name	= lambda *a, **kw: (a, kw),
			is_allowed	= lambda *a: True,
			get_context	= lambda: o,
		)
		o = model.Object(e)
		v = model.Verb(o)
		v.set_id(2048)
		
		self.failUnlessEqual(v.add_name('look'), ((2048, 'look'), {}))
	
	def test_remove_name(self):
		e = test.Anything(
			get_context		= lambda: None,
			get_verb_names	= lambda i: [],
			remove_verb_name	= lambda *a: self.failUnlessEqual(a, (2048, 'test'))
		)
		o = model.Object(e)
		o.set_id(1024)
		v = model.Verb(o)
		v.set_id(2048)
		
		v.remove_name('test')
	
	def test_basic(self):
		e = test.Anything(
			is_allowed	= lambda *a: True,
			get_context	= lambda: o,
			save		= lambda s: True,
		)
		o = model.Object(e)
		v = model.Verb(o)
		
		v.set_code('test code')
		self.failUnlessEqual(v.get_code(), 'test code')
		self.failUnlessEqual(v.code, 'test code')
		
		v.set_ability(True)
		self.failUnlessEqual(v.ability, True)
		self.failUnlessEqual(v.is_ability(), True)
		
		v.set_ability(False)
		self.failUnlessEqual(v.ability, False)
		self.failUnlessEqual(v.is_ability(), False)
		
		v.set_method(True)
		self.failUnlessEqual(v.method, True)
		self.failUnlessEqual(v.is_method(), True)
		
		v.set_method(False)
		self.failUnlessEqual(v.method, False)
		self.failUnlessEqual(v.is_method(), False)
	
	def test_check(self):
		e = test.Anything(
			is_allowed	= lambda *a: False,
			get_context	= lambda: ctx,
		)
		ctx = model.Object(e)
		
		o = model.Object(e)
		v = model.Verb(o)
		
		self.failUnlessRaises(errors.PermissionError, v.check, 'move', o)
	
	def test_is_executable(self):
		results = [True, False, True]
		e = test.Anything(
			is_allowed	= lambda *a, **kw: results.pop(),
			get_context	= lambda: o,
			instantiate	= lambda *a, **kw: o,
		)
		o = model.Object(e)
		p = model.Property(o)
		
		self.failUnlessEqual(p.is_readable(), True)
		self.failUnlessEqual(p.is_readable(), False)
	
	def test_performable_by(self):
		e = test.Anything(
			get_context		= lambda: None,
			is_allowed		= lambda a,p,s: True,
			save			= lambda i: None,
			instantiate		= lambda *a, **kw: o if a[0] == 'object' else v
		)
		o = model.Object(e)
		o.set_id(1024)
		
		v = model.Verb(o)
		v.set_id(2048)
		
		self.failUnlessEqual(v.performable_by(o), False)
		
		v.method = True
		self.failUnlessEqual(v.performable_by(o), False)
		
		v.method = False
		v.ability = True
		self.failUnlessEqual(v.performable_by(o), True)
		

class PropertyTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
		
	def test_id(self):
		e = test.Anything()
		o = model.Object(e)
		p = model.Property(o)
		p.set_id(1024)
		
		self.failUnlessEqual(p.get_id(), 1024)
		self.failUnlessRaises(RuntimeError, p.set_id, 2048)
	
	def test_origin(self):
		e = test.Anything(
			instantiate	= lambda *a, **kw: (a, kw),
			get_context	= lambda: o,
			is_allowed	= lambda *a: True,
		)
		o = model.Object(e)
		o.set_id(1024)
		p = model.Property(o)
		
		self.failUnlessEqual(p.get_origin(), (('object',), {'id': 1024}))
	
	def test_name(self):
		e = test.Anything(
			get_context	= lambda: o,
			is_allowed	= lambda *a: True,
			save		= lambda s: True,
		)
		o = model.Object(e)
		p = model.Property(o)
		p.set_name('prop')
		
		self.failUnlessEqual(p.get_name(), 'prop')
	
	def test_value(self):
		e = test.Anything(
			get_context	= lambda: o,
			is_allowed	= lambda *a: True,
			save		= lambda s: True,
		)
		o = model.Object(e)
		p = model.Property(o)
		p.set_value('prop')
		
		self.failUnlessEqual(p.get_value(), 'prop')
	
	def test_is_readable(self):
		results = [True, False, True]
		e = test.Anything(
			is_allowed	= lambda *a, **kw: results.pop(),
			get_context	= lambda: o,
			instantiate	= lambda *a, **kw: o,
		)
		o = model.Object(e)
		p = model.Property(o)
		
		self.failUnlessEqual(p.is_readable(), True)
		self.failUnlessRaises(errors.PermissionError, p.get_value)
