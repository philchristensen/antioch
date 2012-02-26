#!/usr/bin/env python

# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

import sys, os

# if(len(sys.argv) > 1 and sys.argv[1] == 'runserver'):
#	print >>sys.stderr, "Please use `twistd antioch` to run the server for this project."
#	sys.exit(1)

def monkey_patch_for_multi_threaded():
	# This monkey-patches BaseHTTPServer to create a base HTTPServer class that 
	# supports multithreading 
	import BaseHTTPServer, SocketServer	 
	OriginalHTTPServer = BaseHTTPServer.HTTPServer
	
	class ThreadedHTTPServer(SocketServer.ThreadingMixIn, OriginalHTTPServer):	
		def __init__(self, server_address, RequestHandlerClass=None):  
			OriginalHTTPServer.__init__(self, server_address, RequestHandlerClass)	
	
	BaseHTTPServer.HTTPServer = ThreadedHTTPServer

from antioch import conf
conf.init()

# some debug pages use this variable (improperly, imho)
from django.conf import settings
settings.SETTINGS_MODULE = 'antioch.settings'

def main():
	monkey_patch_for_multi_threaded()
	
	from django.core import management
	u = management.ManagementUtility(sys.argv)
	u.execute()

if(__name__ == '__main__'):
	main()