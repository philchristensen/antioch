# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
General utilities.
"""

import logging, time

def profile(f):
	log = logging.getLogger('antioch.profiler')
	def _f(*args, **kwargs):
		t = time.time()
		result = f(*args, **kwargs)
		log.debug('%r(%s, %s): %f' % (f, args, kwargs, time.time() - t))
		return result
	return _f