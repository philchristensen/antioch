# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Initialization code for child processes.
"""

import warnings
import sys
import logging

from antioch import conf
conf.init('/etc/antioch.yaml', package='antioch.conf', initLogging=False)

TO_CHILD = 3
FROM_CHILD = 4

def initialize():
	from twisted.python import log
	observer = PlainObserver()
	log.startLoggingWithObserver(observer.emit, setStdout=False)
	
	# sys.stdout = log.logfile
	# sys.stderr = log.logerr
	# StdioOnnaStick
	
	ampChildPath = sys.argv[-1]
	
	from twisted.internet import reactor, stdio
	from twisted.python import reflect, runtime
	
	ampChild = reflect.namedAny(ampChildPath)
	ampChildInstance = ampChild(*sys.argv[1:-2])
	if runtime.platform.isWindows():
		stdio.StandardIO(ampChildInstance)
	else:
		stdio.StandardIO(ampChildInstance, TO_CHILD, FROM_CHILD)
	enter = getattr(ampChildInstance, '__enter__', None)
	if enter is not None:
		enter()
	try:
		reactor.run()
	except:
		if enter is not None:
			info = sys.exc_info()
			if not ampChildInstance.__exit__(*info):
				raise
		else:
			raise
	else:
		if enter is not None:
			ampChildInstance.__exit__(None, None, None)
	
	if(conf.get('suppress-deprecation-warnings')):
		import warnings
		warnings.filterwarnings('ignore', r'.*', DeprecationWarning)

class PlainObserver:
	def emit(self, eventDict):
		sys.stderr.write(eventDict['message'][0])
		sys.stderr.flush()

	def start(self):
		from twisted.python import log
		log.addObserver(self.emit)

	def stop(self):
		from twisted.python import log
		log.removeObserver(self.emit)
