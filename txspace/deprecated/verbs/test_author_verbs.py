# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

import unittest

from txspace import registry, parser, errors, minimal, assets, actions
from txspace.security import Q
from txspace.test import check_for_response

class AuthorVerbTestCase(unittest.TestCase):
	def setUp(self):
		self.registry = registry.Registry()
		minimal.init(self.registry, assets.get_verbdir())
	
	def tearDown(self):
		self.registry = None
	
	def test_dig(self):
		# make me an author child
		phil = self.registry.get('phil')
		phil.set_parent(Q, self.registry.get('class_author'))
		
		# check for no direction
		check_for_response(self, phil,
			'@dig to "Test Room"',
			'In what direction do you want to dig?'
		)
		
		# check for no destination
		check_for_response(self, phil,
			'@dig north',
			'Where do you want to dig north to?'
		)
		
		# check for weird permission case
		phil.set_programmer(Q)
		check_for_response(self, phil,
			'@dig north to "Test Room"',
			'Your room was created, but you do not have permission to create an exit to it from here.'
		)
		
		wizard = self.registry.get('wizard')
		
		# normal dig result
		next_id = self.registry.size()
		check_for_response(self, wizard,
			'@dig north to "Another Room"',
			"You created an exit to #%s (Another Room) in the 'north' direction." % next_id
		)
		
		# check exit properties
		room = wizard.get_location(Q)
		self.failUnless(room.has_property(Q, 'exits', recurse=False))
		exits = room.get_property(Q, 'exits')
		self.failUnless('north' in exits)
		new_room = self.registry.get('Another Room')
		self.failUnlessEqual(new_room, exits['north'])
	
	def test_tunnel(self):
		wizard = self.registry.get('wizard')
		
		# create a new room, and put me in it
		another_room = self.registry.new('Another Room')
		wizard.set_location(Q, self.registry.get("Another Room"))
		
		# check for missing direction
		check_for_response(self, wizard,
			'@tunnel to "The Laboratory"',
			'In what direction do you want to tunnel?'
		)
		
		# check for missing destination
		check_for_response(self, wizard,
			'@tunnel south',
			'Where do you want to dig south to?'
		)
		
		# check normal tunnel
		check_for_response(self, wizard,
			'@tunnel south to "The Laboratory"',
			"You created an exit to #10 (The Laboratory) in the 'south' direction."
		)
		
		# check properties
		self.failUnless(another_room.has_property(Q, 'exits', recurse=False))
		exits = another_room.get_property(Q, 'exits')
		self.failUnless('south' in exits)
		classroom = self.registry.get('The Laboratory')
		self.failUnlessEqual(classroom, exits['south'])
	
	def test_alias_exit(self):
		wizard = self.registry.get('wizard')
		classroom = self.registry.get('The Laboratory')
		
		# dig a new room
		next_id = self.registry.size()
		check_for_response(self, wizard,
			'@dig north to "Another Room"',
			"You created an exit to #%s (Another Room) in the 'north' direction." % next_id
		)
		
		# check for missing alias name
		check_for_response(self, wizard,
			'@alias-exit to north',
			"What do you want to call this exit?"
		)
		
		# check for missing referent
		check_for_response(self, wizard,
			'@alias-exit stone archway',
			"What exit do you want this to be an alias for?"
		)
		
		# check normal alias exit
		check_for_response(self, wizard,
			'@alias-exit stone archway to north',
			"Sucessfully created alias stone archway to exit north."
		)
		
		# check properties
		self.failUnless(classroom.has_property(Q, 'exit_aliases', recurse=False))
		aliases = classroom.get_property(Q, 'exit_aliases')
		self.failUnless('stone archway' in aliases)
		self.failUnlessEqual('north', aliases['stone archway'])
	
	def test_alias(self):
		wizard = self.registry.get('wizard')
		classroom = self.registry.get('The Laboratory')
		
		# check for missing object
		check_for_response(self, wizard,
			'@alias to creepy mask',
			"What do you want to create an alias to?"
		)
		
		# check for missing alias name
		check_for_response(self, wizard,
			'@alias mask',
			"What do you want to call it?"
		)
		
		# check for normal success
		check_for_response(self, wizard,
			'@alias mask to creepy mask',
			"Sucessfully created alias creepy mask to #9 (mask)."
		)
		
		# check properties
		mask = self.registry.get('mask')
		self.failUnless(mask.has_property(Q, 'aliases', recurse=False))
		aliases = mask.get_property(Q, 'aliases')
		self.failUnless('creepy mask' in aliases)
	
	def test_create(self):
		wizard = self.registry.get('wizard')
		classroom = self.registry.get('The Laboratory')
		
		check_for_response(self, wizard,
			'@create',
			"What do you want to create?"
		)
		
		next_id = self.registry.size()
		check_for_response(self, wizard,
			'@create thingy',
			"You have created #%s (thingy)" % next_id
		)
		
		thingy = self.registry.get('thingy')
		self.failUnlessEqual(thingy.get_location(Q), wizard.get_location(Q))
		
	def test_describe(self):
		wizard = self.registry.get('wizard')
		
		check_for_response(self, wizard,
			'@describe as something',
			"What do you want to describe?"
		)
		
		check_for_response(self, wizard,
			'@describe wizard',
			"How do you want to describe wizard?"
		)
		
		check_for_response(self, wizard,
			'@describe mask as "some cruddy mask"',
			"Description of #9 (mask) set to 'some cruddy mask'"
		)
		
		mask = self.registry.get('mask')
		
		self.failUnless(mask.has_property(Q, 'description', recurse=False))
		self.failUnlessEqual(mask.get_property(Q, 'description'), 'some cruddy mask')