#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: programmer_edit_acl.py 184 2007-03-04 18:54:05Z phil $
#
# See LICENSE for details

if not(has_dobj_str()):
	caller.write("What object do you want to edit the ACL for?")
	return
acl = None
if(has_pobj_str("on")):
	if(has_pobj("on")):
		obj = get_pobj("on")
	else:
		obj = get_obj(get_pobj_str("on"))
	if(obj._vdict.has_key(get_dobj_str())):
		obj = obj._vdict[get_dobj_str()]
	else:
		raise errors.UserError, "There is no verb or property called '%s' on '%s'!" % (get_dobj_str(), str(obj))
else:
	if(has_dobj()):
		obj = get_dobj()
	else:
		obj = get_obj(get_dobj_str())
edit_acl(caller, obj)
