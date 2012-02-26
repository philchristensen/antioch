# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Log customization support.
"""

import sys, re, time, logging

import simplejson

from twisted.python import log
from twisted.web import server

from django.utils import termcolors

styles = dict(
	ERROR = termcolors.make_style(fg='red', opts=['bold']),
	WARNING = termcolors.make_style(fg='yellow', opts=['bold']),
	INFO = termcolors.make_style(fg='cyan'),
	DEBUG = termcolors.make_style(fg='blue'),
)

class DjangoColorFormatter(object):
	def __init__(self, logformat=None, datefmt=None):
		self.logformat = logformat if logformat else '[%(asctime)s] %(levelname)s: %(msg)s'
		self.datefmt = datefmt if datefmt else '%d/%b/%Y %H:%M:%S'
	
	def format(self, log):
		supports_color = True
		unsupported_platform = (sys.platform in ('win32', 'Pocket PC'))
		is_a_tty = hasattr(sys.__stdout__, 'isatty') and sys.__stdout__.isatty()
		
		result = self.logformat % dict(
			asctime = time.strftime(self.datefmt, time.gmtime(log.created)),
			**log.__dict__
		)
		
		if log.levelname not in styles or unsupported_platform or not is_a_tty:
			return result
		else:
			return styles[log.levelname](result)

class JSONFormatter(object):
	def format(self, log):
		return simplejson.dumps(dict(
			name		= log.name,
			levelname	= log.levelname,
			msg			= str(log.msg),
		))

class AccessLoggingSite(server.Site):
	def __init__(self, resource, logPath=None, timeout=60*60*12):
		# get around the superclass constructor checking for a string for no reason
		server.Site.__init__(self, resource, '/dev/null', timeout)
		self.logPath = logPath
	
	def _openLogFile(self, path):
		if(isinstance(path, basestring)):
			f = open(path, "a", 1)
			return f
		elif(hasattr(path, 'read')):
			return path
		else:
			raise ValueError("Unexpected logFile argument: %r" % path)

class AccessLogOnnaStick(log.StdioOnnaStick):
	def __init__(self, loggerName):
		log.StdioOnnaStick.__init__(self)
		self.log = logging.getLogger(loggerName)
	
	def write(self, data):
		if isinstance(data, unicode):
			data = data.encode(self.encoding)
		d = (self.buf + data).split('\n')
		self.buf = d[-1]
		messages = d[0:-1]
		for message in messages:
			self.log.info(message)
	
	def writelines(self, lines):
		for line in lines:
			if isinstance(line, unicode):
				line = line.encode(self.encoding)
			self.log.info(line)

