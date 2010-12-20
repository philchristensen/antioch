#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: programmer_eval.py 33 2006-04-16 20:54:45Z phil $
#
# See LICENSE for details

result = eval(command[command.find(" ") + 1:],)
caller.write(result)
