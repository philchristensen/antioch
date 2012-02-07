# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Initialization code for child processes.
"""

import warnings

from antioch import conf
#from antioch.util import logging

conf.init('/etc/antioch.yaml', package='antioch.conf')

def initialize():
	if(conf.get('suppress-deprecation-warnings')):
		import warnings
		warnings.filterwarnings('ignore', r'.*', DeprecationWarning)

	# if not(conf.get('error-log')):
	# 	logging.customizeLogs()

