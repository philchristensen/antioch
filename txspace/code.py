# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Code
"""

from txspace import errors

def r_eval(code, environment):
	if not(environment):
		raise RuntimeError('No environment')
	return eval(code, environment)

def r_exec(code, environment):
	if not(environment):
		raise RuntimeError('No environment')
	exec(code, environment)
	if("__result__" in environment):
		return environment["__result__"]

