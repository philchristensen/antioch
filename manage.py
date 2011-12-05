#!/usr/bin/env python

# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

import sys, os

if(len(sys.argv) > 1 and sys.argv[1] == 'runserver'):
	print >>sys.stderr, "Please use `twistd antioch` to run the server for this project."
	sys.exit(1)

from antioch import conf
conf.init()

# some debug pages use this variable (improperly, imho)
from django.conf import settings
settings.SETTINGS_MODULE = 'antioch.settings'

from django.core import management
u = management.ManagementUtility(sys.argv)
u.execute()