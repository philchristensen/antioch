# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
# See LICENSE for details

import unittest, string

from txspace import registry, errors, security, entity
from txspace.security import Q

class ACLTestCase(unittest.TestCase):
	def setUp(self):
		self.registry = registry.Registry()
		self.phil = self.registry.new("phil")
		self.bill = self.registry.new("bill")
		self.jim = self.registry.new("jim")
		self.bob = self.registry.new("bob")
	
	def tearDown(self):
		self.registry = None
		self.phil = None
		self.bill = None
		self.jim = None
		self.bob = None
	
	def test_acl(self):
		def includes_bob(obj):
			if(obj.get_name(Q) is "bob"):
				return True
			return False
		acl = self.registry.new('acl')
		acl.set_owner(Q, self.phil)
		
		security.allow(self.jim, "access_jim", acl)
		security.allow(self.phil, "access_owner", acl)
		security.allow('everyone', "access_everyone", acl)
		assert security.is_allowed(self.jim, "access_jim", acl), "jim not allowed access_jim"
		assert security.is_allowed(self.phil, "access_owner", acl), "phil not allowed access_owner"
		assert security.is_allowed(self.bill, "access_everyone", acl), "bill not allowed access_everyone"
		assert security.is_allowed(self.phil, "access_jim", acl), "phil allowed access_jim"
		assert not security.is_allowed(self.jim, "access_owner", acl), "jim allowed access_owner"

if __name__ == "__main__":
	unittest.main()
