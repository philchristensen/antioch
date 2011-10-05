# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Implements Athena support on the client.
"""

from nevow import athena
from antioch import assets

myPackage = athena.JSPackage({
    'antioch': assets.get('webroot/js/client.js'),
    })

