# antioch
# Copyright (c) 1999-2018 Phil Christensen
#
#
# See LICENSE for details

"""
General utilities.
"""

import logging, time, string, crypt, random

salt_data = list(string.ascii_letters[:])

def profile(f):
    log = logging.getLogger('antioch.profiler')
    def _f(*args, **kwargs):
        t = time.time()
        result = f(*args, **kwargs)
        log.debug('%r(%s, %s): %f' % (f, args, kwargs, time.time() - t))
        return result
    return _f

def hash_password(passwd, salt=None):
    random.shuffle(salt_data)
    salt = salt or ''.join(salt_data[0:2])
    return crypt.crypt(passwd, salt)