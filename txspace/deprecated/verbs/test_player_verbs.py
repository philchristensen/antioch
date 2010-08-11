# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

import unittest

from txspace import registry, parser, errors, minimal, assets, actions
from txspace.security import Q
from txspace.test import check_for_response, check_for_observation, WriteConnection

class PlayerVerbTestCase(unittest.TestCase):
	def setUp(self):
		self.registry = registry.Registry()
		minimal.init(self.registry, assets.get_verbdir())
	
	def tearDown(self):
		self.registry = None
	
	def test_hear(self):
		wizard = self.registry.get('wizard')
		phil = self.registry.get('phil')
		phil.set_connection(Q, WriteConnection())
		
		try:
			phil.call_verb(wizard, 'hear', wizard, 'something', False)
		except errors.TestError, e:
			self.failUnlessEqual(e.data, 'wizard says, "something"')
		else:
			self.fail("Didn't hear anything.")
		
		try:
			phil.call_verb(wizard, 'hear', wizard, 'something', True)
		except errors.TestError, e:
			self.failUnlessEqual(e.data, 'wizard says, "something" to you.')
		else:
			self.fail("Didn't hear anything.")
	
	def test_look(self):
		phil = self.registry.get('phil')
		self.looked = False
		
		def look_here(obs):
			self.failUnlessEqual(obs['name'], 'The Laboratory')
			self.looked = True
		
		check_for_observation(self, phil,
			'look',
			look_here
		)
		self.failUnless(self.looked)
		
		wizard = self.registry.get('phil')
		wizard.set_connection(Q, WriteConnection())
		
		self.looked = False
		def look_wizard(obs):
			self.failUnlessEqual(obs['name'], 'wizard')
			self.failIfEqual(obs['description'], "There doesn't seem to be anything special about wizard.")
			self.looked = True
		
		check_for_observation(self, phil,
			'look wizard',
			look_wizard,
		)
		
		self.failUnless(self.looked)
	
	def test_give(self):
		phil = self.registry.get('phil')
		mask = self.registry.get('mask')
		box = self.registry.new('box')
		box.set_location(Q, phil)
		
		# check for missing direct object
		check_for_response(self, phil,
			'give',
			'What do you want to give?',
		)
		
		# check for missing direct object
		check_for_response(self, phil,
			'give mask',
			'Who do you want to give %s to?' % mask,
		)
		check_for_response(self, phil,
			'put mask',
			'Where do you want to put %s?' % mask,
		)
		check_for_response(self, phil,
			'drop my box',
			"#8 (phil) is not allowed to 'set_location' on #12 (box)",
		)
		
		wizard = self.registry.get('wizard')
		mask.set_location(Q, wizard)
		check_for_response(self, wizard,
			'give my mask to phil',
			'You gave #8 (phil) your #9 (mask)' % mask,
		)
		self.failUnlessEqual(mask.get_location(Q), phil)
		
		mask.set_location(Q, wizard)
		box.set_location(Q, wizard.get_location(Q))
		check_for_response(self, wizard,
			'put my mask in box',
			"You put your #9 (mask) into #12 (box)",
		)
		self.failUnlessEqual(mask.get_location(Q), box)
		
		box.set_location(Q, wizard)
		check_for_response(self, wizard,
			'drop my box',
			"You drop your #12 (box) in #10 (The Laboratory)",
		)
		self.failUnlessEqual(box.get_location(Q), wizard.get_location(Q))
		
		mask.set_location(Q, wizard)
		check_for_response(self, wizard,
			'give my mask to box',
			"#12 (box) can't take your #9 (mask)",
		)
		
		check_for_response(self, wizard,
			'put box on phil',
			"You can't put #12 (box) onto #8 (phil)",
		)
	
		check_for_response(self, wizard,
			'put my mask in phil',
			"You can't put your #9 (mask) into #8 (phil)",
		)
	
	def test_go(self):
		phil = self.registry.get('phil')
		
		# check for missing directions
		check_for_response(self, phil,
			'go',
			'Where do you want to go?',
		)
		
		# check for no existing directions
		check_for_response(self, phil,
			'go fake-direction',
			"You can't go that way.",
		)
		
		# create an exit
		another_room = self.registry.new('Another Room')
		room = phil.get_location(Q)
		another_room.add_property(Q, 'exits', {'south':room}, owner=phil)
		room.add_property(Q, 'exits', {'north':another_room}, owner=phil)
		
		# check for fake direction
		check_for_response(self, phil,
			'go fake-direction',
			"You can't go that way.",
		)
		
		# check for basic movement
		check_for_response(self, phil,
			'go north',
			None,
		)
		self.failUnlessEqual(phil.get_location(Q), another_room)
		
		# go back to start, check again
		check_for_response(self, phil,
			'go south',
			None,
		)
		self.failUnlessEqual(phil.get_location(Q), room)
		
		# check exit aliases
		room.add_property(Q, 'exit_aliases', {'stone archway':'north'}, owner=phil)
		check_for_response(self, phil,
			'go stone archway',
			None,
		)
		self.failUnlessEqual(phil.get_location(Q), another_room)

		# go back to start, check again
		check_for_response(self, phil,
			'go south',
			None,
		)
		self.failUnlessEqual(phil.get_location(Q), room)
		
		# create a door
		door = self.registry.new('giant wooden door')
		door.set_parent(Q, self.registry.get('class_door'))
		door.add_verb(Q, 'return False', ['enter'], owner=phil)
		door.add_property(Q, 'target', another_room, owner=phil)
		room.set_property(Q, 'exits', {'north':door})
		
		# door is locked
		check_for_response(self, phil,
			'go north',
			"%s appears to be locked." % door,
		)
		self.failIfEqual(phil.get_location(Q), another_room)
		
		# go through the door (location not set because of test harness)
		door.remove_verb(Q, 'enter')
		check_for_response(self, phil,
			'go north',
			'You go through the %s' % door,
		)
		self.failIfEqual(phil.get_location(Q), another_room)
		
		# override the enter verb to check door
		door.add_verb(Q, 'return True', ['enter'], owner=phil)
		check_for_response(self, phil,
			'go north',
			None,
		)
		self.failUnlessEqual(phil.get_location(Q), another_room)
