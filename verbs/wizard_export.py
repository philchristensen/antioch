#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: wizard_export.py 159 2007-02-14 03:47:03Z phil $
#
# See LICENSE for details

from inner.space import external, auth

datafile = file(get_dobj_str(), 'w')
external.export(auth.get_registry(), datafile)
datafile.close()

caller.write("The registry was successfully exported to " + datafile.name)