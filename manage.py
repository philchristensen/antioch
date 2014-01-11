#!/usr/bin/env python

# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

import os
import sys

def monkey_patch_for_multi_threaded():
	# This monkey-patches BaseHTTPServer to create a base HTTPServer class that 
	# supports multithreading 
	import BaseHTTPServer, SocketServer	 
	OriginalHTTPServer = BaseHTTPServer.HTTPServer
	
	class ThreadedHTTPServer(SocketServer.ThreadingMixIn, OriginalHTTPServer):	
		def __init__(self, server_address, RequestHandlerClass=None):  
			OriginalHTTPServer.__init__(self, server_address, RequestHandlerClass)	
	
	BaseHTTPServer.HTTPServer = ThreadedHTTPServer

if __name__ == "__main__":
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "antioch.settings")

	from django.core.management import execute_from_command_line

	execute_from_command_line(sys.argv)
