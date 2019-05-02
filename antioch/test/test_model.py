# antioch
# Copyright (c) 1999-2019 Phil Christensen
#
# See LICENSE for details

from django.test import TestCase

from antioch import test
from antioch.core import interface, errors

class EntityTestCase(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_id(self):
        e = test.Anything()
        o = interface.Object(e)
        o.set_id(1024)
        
        self.assertEqual(o.get_id(), 1024)
        self.assertEqual(o.id, 1024)
        self.assertRaises(RuntimeError, o.set_id, 2048)
        
    def test_owner(self):
        e = test.Anything(
            instantiate    = lambda *a, **kw: owner,
            get_context    = lambda: None,
            save        = lambda s: True,
        )
        
        owner = interface.Object(e)
        owner_mock = test.Anything(
            get_id    = lambda: 1024,
        )
        subject = interface.Object(e)
        subject2 = interface.Property(subject)
        subject3 = interface.Verb(subject)
        
        subject.set_owner(owner_mock)
        self.assertEqual(subject.get_owner(), owner)
        self.assertEqual(subject.owner, owner)
        
        subject2.set_owner(owner_mock)
        self.assertEqual(subject2.get_owner(), owner)
        self.assertEqual(subject2.owner, owner)
        
        subject3.set_owner(owner_mock)
        self.assertEqual(subject3.get_owner(), owner)
        self.assertEqual(subject3.owner, owner)
    
    def test_origin(self):
        e = test.Anything(
            instantiate    = lambda *a, **kw: origin,
            get_context    = lambda: None,
        )
        
        origin = interface.Object(e)
        p = interface.Property(origin)
        
        self.assertEqual(p.get_origin(), origin)
        self.assertEqual(p.origin, origin)
        
        v = interface.Verb(origin)
        self.assertEqual(v.get_origin(), origin)
        self.assertEqual(v.origin, origin)
    
    def test_get_exchange(self):
        e = test.Anything()
        o = interface.Object(e)
        self.assertEqual(o.get_exchange(), e)
    
    def test_get_context(self):
        e = test.Anything(
            get_context    = lambda: o
        )
        o = interface.Object(e)
        self.assertEqual(o.get_context(), o)
    
    def test_get_obj_details(self):
        e = test.Anything(
            get_context            = lambda: None,
            save                = lambda x: None,
            is_unique_name        = lambda n: False,
            get_details            = lambda *a, **kw: self.assertEqual((a,kw), ''),
            get_parents            = lambda i, r: [],
            get_verb_list        = lambda i: [],
            get_property_list    = lambda i: [],
        )
        o = interface.Object(e)
        o.set_id(1024)
        o.set_name('test object', real=True)
        
        details = o.get_details()
        self.assertEqual(details, dict(
            __str__     = '#1024 (test object)',
            id            = 1024,
            kind        = 'object',
            location    = 'None',
            name        = 'test object',
            owner        = 'None',
            parents        = '',
            properties    = [],
            verbs        = [],
        ))
    
    def test_get_verb_details(self):
        e = test.Anything(
            get_context            = lambda: None,
            # save                = lambda x: None,
            # is_unique_name        = lambda n: False,
            # get_details            = lambda *a, **kw: self.assertEqual((a,kw), ''),
            get_parents            = lambda i, r: [],
            get_verb_list        = lambda i: [],
            get_property_list    = lambda i: [],
            get_verb_names        = lambda i: ['test'],
            add_verb_name        = lambda i, n: self.assertEqual(n, 'test'),
            instantiate            = lambda *a, **kw: o if a[0] == 'object' else v,
        )
        o = interface.Object(e)
        o.set_id(1024)
        v = interface.Verb(o)
        v.set_names(['test'])
        
        details = v.get_details()
        self.assertEqual(details, dict(
            __str__     = 'Verb test {#0 on #1024 ()}',
            id          = 0,
            kind        = 'verb',
            code        = '',
            exec_type   = 'verb',
            names       = ['test'],
            owner       = 'None',
            origin       = '#1024 ()',
        ))
        
    def test_save(self):
        e = test.Anything(
            save = lambda x: test.raise_e(errors.TestError())
        )
        o = interface.Object(e)
        self.assertRaises(errors.TestError, o.save)
    
    def test_destroy(self):
        e = test.Anything(
            destroy        = lambda x: test.raise_e(errors.TestError()),
            get_context = lambda: None,
        )
        o = interface.Object(e)
        self.assertRaises(errors.TestError, o.destroy)

class ObjectTestCase(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_owns(self):
        e = test.Anything(
            get_context    = lambda: None,
            save        = lambda x: None,
            instantiate    = lambda *a, **kw: owner if kw['id'] == 1024 else subject,
        )
        owner = interface.Object(e)
        owner.set_id(1024)
        subject = interface.Object(e)
        subject.set_id(2048)
        subject.set_owner(owner)
        
        self.assertEqual(owner.owns(subject), True)
    
    def test_verb(self):
        e = test.Anything(
            get_verb    = lambda *a, **kw: v,
            get_context    = lambda: o,
            is_allowed    = lambda *a: True,
        )
        o = interface.Object(e)
        v = interface.Verb(o)
        self.assertEqual(getattr(o, 'look'), v)
        self.assertEqual(o.get_verb('look', recurse=False), v)
    
    def test_add_verb(self):
        x = test.Anything(
            get_id        = lambda: -1,
        )
        e = test.Anything(
            instantiate    = lambda *a, **kw: v,
            get_context    = lambda: o,
            ctx            = x,
            is_allowed    = lambda *a: True,
            is_wizard    = lambda *a: False,
        )
        o = interface.Object(e)
        v = interface.Verb(o)
        
        self.assertEqual(o.add_verb('look'), v)
    
    def test_has_verb(self):
        e = test.Anything(
            has        =    lambda *a, **kw: (a, kw),
        )
        o = interface.Object(e)
        o.set_id(1024)
        v = test.Anything(
        )
        
        self.assertEqual(o.has_verb('look'), ((1024, 'verb', 'look'), {}))
        self.assertEqual(o.has_callable_verb('look'), ((1024, 'verb', 'look'), {'unrestricted': False}))
    
    def test_remove_verb(self):
        e = test.Anything(
            get_context        = lambda: None,
            remove_verb        = lambda *a, **kw: self.assertEqual(kw, {'name': 'test', 'origin_id': 1024})
        )
        o = interface.Object(e)
        o.set_id(1024)
        
        o.remove_verb('test')
    
    def test_get_property(self):
        e = test.Anything(
            get_property    = lambda *a, **kw: p,
            get_context        = lambda: o,
            is_allowed        = lambda *a: True,
        )
        o = interface.Object(e)
        p = test.Anything(
            origin        = lambda: o,
            get_type    = lambda: 'string',
            get_id        = lambda: -1,
        )
        
        self.assertEqual(o['description'], p)
        self.assertEqual(o.get_property('description'), p)
    
    def test_add_property(self):
        class _PropertyAdded(Exception):
            pass
        
        def _err(name):
            raise _PropertyAdded(name)
        
        x = test.Anything(
            get_id        = lambda: -1
        )
        e = test.Anything(
            instantiate    = lambda *a, **kw: p,
            get_context    = lambda: o,
            is_allowed    = lambda *a: True,
            is_wizard    = lambda *a: False,
        )
        o = interface.Object(e)
        o.set_id(1024)
        p = test.Anything(
            origin    = lambda: o
        )
        
        self.assertEqual(o.add_property('description'), p)
    
    def test_has_property(self):
        results = [False, True, True]
        e = test.Anything(
            has        =    lambda *a, **kw: results.pop(),
        )
        o = interface.Object(e)
        o.set_id(1024)
        v = test.Anything(
        )
        
        self.assertEqual('description' in o, True)
        self.assertEqual(o.has_property('description'), True)
        self.assertEqual(o.has_readable_property('description'), False)
    
    def test_remove_property(self):
        e = test.Anything(
            get_context        = lambda: None,
            remove_property    = lambda **kw: self.assertEqual(kw, {'name': 'test', 'origin_id': 1024})
        )
        o = interface.Object(e)
        o.set_id(1024)
        
        o.remove_property('test')
    
    def test_get_ancestor_with(self):
        e = test.Anything(
            get_context        = lambda: None,
            get_ancestor_with    = lambda *a: self.assertEqual(a, (1024, 'verb', 'test'))
        )
        o = interface.Object(e)
        o.set_id(1024)
        
        o.get_ancestor_with('verb', 'test')
    
    def test_is_player(self):
        e = test.Anything(
            is_player    =    lambda *a, **kw: (a, kw),
        )
        o = interface.Object(e)
        o.set_id(1024)
        
        self.assertEqual(o.is_player(),  ((1024,), {}))
    
    def test_is_connected_player(self):
        e = test.Anything(
            get_context        = lambda: None,
            is_connected_player    = lambda *a, **kw: self.assertEqual(a[0], 1024)
        )
        o = interface.Object(e)
        o.set_id(1024)
        
        o.is_connected_player()
    
    def test_set_player(self):
        e = test.Anything(
            get_context        = lambda: None,
            set_player    = lambda *a, **kw: self.assertEqual(a, (1024,))
        )
        o = interface.Object(e)
        o.set_id(1024)
        
        o.set_player(True, True, 'passwd')
    
    def test_name(self):
        uniques = [False, True]
        hases = [True, True, False, False, False]
        e = test.Anything(
            is_unique_name        = lambda name: uniques.pop(),
            has                    = lambda *a, **kw: hases.pop(),
            instantiate            = lambda *a, **kw: p,
            get_property        = lambda *a, **kw: p,
            get_context            = lambda: o,
            is_allowed            = lambda *a: True,
            is_wizard            = lambda *a: False,
            save                = lambda s: True,
        )
        e.ctx = test.Anything(
            get_id                =    lambda: -1
        )
        
        o = interface.Object(e)
        p = interface.Property(o)
        
        self.assertRaises(ValueError, o.set_name, 'phil', real=True)
        o.set_name('phil', real=True)
        
        #import pdb; pdb.set_trace()
        self.assertEqual(o.get_name(), 'phil')
        self.assertEqual(o.name, 'phil')
        
        o.set_name('phil-prop')
        
        self.assertEqual(o.get_name(real=True), 'phil')
        self.assertEqual(o.get_name(), 'phil-prop')
        self.assertEqual(o.name, 'phil-prop')
        
    
    def test_location(self):
        contained = [False, True]
        e = test.Anything(
            instantiate    = lambda *a, **kw: room,
            contains    = lambda *a, **kw: contained.pop(),
            get_context    = lambda: subject,
            is_allowed    = lambda *a: True,
            is_wizard    = lambda *a: False,
            is_player    = lambda *a: False,
            save        = lambda s: True,
            clear_observers    = lambda s: None,
        )
        room = interface.Object(e)
        room_mock = test.Anything(
            get_id    = lambda: 1024,
            has_verb = lambda v: None,
            notify_observers = lambda: None,
        )
        subject = interface.Object(e)
        
        self.assertRaises(errors.RecursiveError, subject.set_location, room_mock)
        
        subject.set_location(room_mock)
        self.assertEqual(subject.get_location(), room)
        self.assertEqual(subject.location, room)
    
    def test_find(self):
        e = test.Anything(
            get_context        = lambda: None,
            find            = lambda *a: self.assertEqual(a, (1024, 'thing'))
        )
        container = interface.Object(e)
        container.set_id(1024)
        
        container.find('thing')
    
    def test_contains(self):
        e = test.Anything(
            get_context        = lambda: None,
            contains        = lambda *a: self.assertEqual(a, (1024, 2048, True))
        )
        container = interface.Object(e)
        container.set_id(1024)
        thing = interface.Object(e)
        thing.set_id(2048)
        
        container.contains(thing)
    
    def test_get_contents(self):
        e = test.Anything(
            get_context        = lambda: None,
            get_contents    = lambda *a: self.assertEqual(a[0], 1024)
        )
        container = interface.Object(e)
        container.set_id(1024)
        
        container.get_contents()
    
    def test_parent(self):
        e = test.Anything(
            add_parent    = lambda *a, **kw: (a, kw),
            get_parents = lambda *a, **kw: [parent],
            has_parent    = lambda p, r: True,
            get_context    = lambda: child,
            is_allowed    = lambda *a: True,
            is_wizard    = lambda *a: False,
        )
        child = interface.Object(e)
        child.set_id(1024)
        
        child_mock = test.Anything(
            has_parent    = lambda p: True,
            get_id        = lambda: parent.get_id(),
        )
        
        parent = interface.Object(e)
        parent.set_id(2048)
        
        parent_mock = test.Anything(
            has_parent    = lambda p: False,
            get_id        = lambda: parent.get_id(),
            get_type    = lambda: 'object',
            get_owner    = lambda: parent_mock,
        )
        
        child.add_parent(parent_mock)
        self.assertRaises(errors.RecursiveError, parent.add_parent, child)
        self.assertEqual(child.get_parents(), [parent])
    
    def test_remove_parent(self):
        e = test.Anything(
            get_context        = lambda: None,
            remove_parent    = lambda *a: self.assertEqual(a, (2048, 1024))
        )
        child = interface.Object(e)
        child.set_id(1024)
        parent = interface.Object(e)
        parent.set_id(2048)
        
        child.remove_parent(parent)
    
    def test_check(self):
        allowances = [True, False]
        e = test.Anything(
            is_allowed    = lambda *a: allowances.pop(),
            get_context    = lambda: ctx,
            is_wizard    = lambda *a: False,
        )
        ctx = interface.Object(e)
        
        person = interface.Object(e)
        item = interface.Object(e)
        
        self.assertRaises(errors.PermissionError, person.check, 'move', item)
        self.assertEqual(person.is_allowed('move', item), True)
    

class VerbTestCase(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_id(self):
        e = test.Anything()
        o = interface.Object(e)
        v = interface.Verb(o)
        v.set_id(1024)
        
        self.assertEqual(v.get_id(), 1024)
        self.assertRaises(RuntimeError, v.set_id, 2048)
    
    def test_origin(self):
        e = test.Anything(
            instantiate    = lambda *a, **kw: (a, kw),
            is_allowed    = lambda *a: True,
            get_context    = lambda: o,
            is_wizard    = lambda *a: False,
        )
        o = interface.Object(e)
        o.set_id(1024)
        v = interface.Verb(o)
        
        self.assertEqual(v.get_origin(), (('object',), {'id': 1024}))
    
    def test_names(self):
        e = test.Anything(
            get_verb_names    = lambda *a, **kw: (a, kw),
        )
        o = interface.Object(e)
        v = interface.Verb(o)
        v.set_id(2048)
        
        self.assertEqual(v.get_names(), ((2048,), {}))
    
    def test_set_names(self):
        e = test.Anything(
            get_context        = lambda: None,
            get_verb_names    = lambda i: [],
            add_verb_name    = lambda *a: self.assertEqual(a, (2048, 'test'))
        )
        o = interface.Object(e)
        o.set_id(1024)
        v = interface.Verb(o)
        v.set_id(2048)
        
        v.set_names(['test'])
    
    def test_add_name(self):
        e = test.Anything(
            add_verb_name    = lambda *a, **kw: (a, kw),
            is_allowed    = lambda *a: True,
            get_context    = lambda: o,
            is_wizard    = lambda *a: False,
        )
        o = interface.Object(e)
        v = interface.Verb(o)
        v.set_id(2048)
        
        self.assertEqual(v.add_name('look'), ((2048, 'look'), {}))
    
    def test_remove_name(self):
        e = test.Anything(
            get_context        = lambda: None,
            get_verb_names    = lambda i: [],
            remove_verb_name    = lambda *a: self.assertEqual(a, (2048, 'test'))
        )
        o = interface.Object(e)
        o.set_id(1024)
        v = interface.Verb(o)
        v.set_id(2048)
        
        v.remove_name('test')
    
    def test_basic(self):
        e = test.Anything(
            is_allowed    = lambda *a: True,
            get_context    = lambda: o,
            save        = lambda s: True,
            is_wizard    = lambda *a: False,
        )
        o = interface.Object(e)
        v = interface.Verb(o)
        
        v.set_code('test code')
        self.assertEqual(v.get_code(), 'test code')
        self.assertEqual(v.code, 'test code')
        
        v.set_ability(True)
        self.assertEqual(v.ability, True)
        self.assertEqual(v.is_ability(), True)
        
        v.set_ability(False)
        self.assertEqual(v.ability, False)
        self.assertEqual(v.is_ability(), False)
        
        v.set_method(True)
        self.assertEqual(v.method, True)
        self.assertEqual(v.is_method(), True)
        
        v.set_method(False)
        self.assertEqual(v.method, False)
        self.assertEqual(v.is_method(), False)
    
    def test_check(self):
        e = test.Anything(
            is_allowed    = lambda *a: False,
            get_context    = lambda: ctx,
            is_wizard    = lambda *a: False,
        )
        ctx = interface.Object(e)
        
        o = interface.Object(e)
        v = interface.Verb(o)
        
        self.assertRaises(errors.PermissionError, v.check, 'move', o)
    
    def test_is_executable(self):
        results = [True, False, True]
        e = test.Anything(
            is_allowed    = lambda *a, **kw: results.pop(),
            get_context    = lambda: o,
            instantiate    = lambda *a, **kw: o,
            is_wizard    = lambda *a: False,
        )
        o = interface.Object(e)
        p = interface.Property(o)
        
        self.assertEqual(p.is_readable(), True)
        self.assertEqual(p.is_readable(), False)
    
    def test_performable_by(self):
        e = test.Anything(
            get_context        = lambda: None,
            is_allowed        = lambda a,p,s: True,
            has_parent        = lambda c,p: False,
            save            = lambda i: None,
            instantiate        = lambda *a, **kw: o if a[0] == 'object' else v
        )
        o = interface.Object(e)
        o.set_id(1024)
        
        v = interface.Verb(o)
        v.set_id(2048)
        
        self.assertEqual(v.performable_by(o), False)
        
        v.method = True
        self.assertEqual(v.performable_by(o), False)
        
        v.method = False
        v.ability = True
        self.assertEqual(v.performable_by(o), True)
        

class PropertyTestCase(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
        
    def test_id(self):
        e = test.Anything()
        o = interface.Object(e)
        p = interface.Property(o)
        p.set_id(1024)
        
        self.assertEqual(p.get_id(), 1024)
        self.assertRaises(RuntimeError, p.set_id, 2048)
    
    def test_origin(self):
        e = test.Anything(
            instantiate    = lambda *a, **kw: (a, kw),
            get_context    = lambda: o,
            is_allowed    = lambda *a: True,
            is_wizard    = lambda *a: False,
        )
        o = interface.Object(e)
        o.set_id(1024)
        p = interface.Property(o)
        
        self.assertEqual(p.get_origin(), (('object',), {'id': 1024}))
    
    def test_name(self):
        e = test.Anything(
            get_context    = lambda: o,
            is_allowed    = lambda *a: True,
            save        = lambda s: True,
            is_wizard    = lambda *a: False,
        )
        o = interface.Object(e)
        p = interface.Property(o)
        p.set_name('prop')
        
        self.assertEqual(p.get_name(), 'prop')
    
    def test_value(self):
        e = test.Anything(
            get_context    = lambda: o,
            is_allowed    = lambda *a: True,
            save        = lambda s: True,
            is_wizard    = lambda *a: False,
        )
        o = interface.Object(e)
        p = interface.Property(o)
        p.set_value('prop')
        
        self.assertEqual(p.get_value(), 'prop')
    
    def test_is_readable(self):
        results = [True, False, True]
        e = test.Anything(
            is_allowed    = lambda *a, **kw: results.pop(),
            get_context    = lambda: o,
            instantiate    = lambda *a, **kw: o,
            is_wizard    = lambda *a: False,
        )
        o = interface.Object(e)
        p = interface.Property(o)
        
        self.assertEqual(p.is_readable(), True)
        self.assertRaises(errors.PermissionError, p.get_value)
