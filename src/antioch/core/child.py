# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Initialization code for child processes.
"""

import warnings
warnings.filterwarnings('ignore', r'.*', UserWarning)

import sys
import logging

import simplejson

from antioch import conf
conf.init('/etc/antioch.yaml', package='antioch.conf', initLogging=False)

TO_CHILD = 3
FROM_CHILD = 4

def bootstrap():
	childArgs = list(sys.argv[1:])
	ampChildPath = childArgs.pop()
	childReactor = childArgs.pop()
	
	# twisted logging
	from twisted.python import log
	observer = JSONObserver()
	log.startLoggingWithObserver(observer.emit, setStdout=False)
	
	# standard python logging
	try:
		from logging.config import dictConfig
	except ImportError:
		from django.utils.log import dictConfig
	dictConfig({
		"version": 1,
		"disable_existing_loggers": False,
		"formatters": {
			"default": {
				"()": "antioch.util.logs.JSONFormatter",
			}
		},
		"handlers": {
			"console": {
				"class": "logging.StreamHandler",
				"formatter": "default",
				"level": "DEBUG",
			}
		},
		'root': {
			'handlers':['console'],
			'level':'DEBUG',
		}
	})
	
	from twisted.internet import reactor, stdio
	from twisted.python import reflect, runtime
	
	ampChild = reflect.namedAny(ampChildPath)
	ampChildInstance = ampChild(*childArgs)
	stdio.StandardIO(ampChildInstance, TO_CHILD, FROM_CHILD)
	
	reactor.run()
	
	if(conf.get('suppress-deprecation-warnings')):
		import warnings
		warnings.filterwarnings('ignore', r'.*', DeprecationWarning)

class JSONObserver:
	def emit(self, eventDict):
		sys.__stderr__.write(simplejson.dumps(eventDict) + "\n")
		sys.__stderr__.flush()

	def start(self):
		from twisted.python import log
		log.addObserver(self.emit)

	def stop(self):
		from twisted.python import log
		log.removeObserver(self.emit)
