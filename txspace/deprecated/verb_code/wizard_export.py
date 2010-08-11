# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

from txspace import external, auth

datafile = file(get_dobj_str(), 'w')
external.export(registry, datafile)
datafile.close()

caller.write("The registry was successfully exported to " + datafile.name)