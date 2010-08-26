# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Editors


Contains the routines to manipulate and interact with the 
object editors provided by the client.
"""

import types, copy

from twisted.internet.defer import inlineCallbacks, returnValue

from txspace import errors, code

#from txspace import security, actions

@inlineCallbacks
def edit_entity(ctx, obj):
	"""
	Present an object editing window for 'obj'
	through the connection to user.
	"""
	from txspace import auth
	security.check_allowed(ctx, 'edit_entity', obj)
	if not(ctx.is_connected_player(ctx)):
		raise errors.PermissionError, "A non-connected-player entity cannot edit an object!"
	
	info = obj.get_details(ctx)
	
	response = yield ctx._connection.open_editor('obj', info)
	if(response):
		obj.set_details(ctx, response)

@inlineCallbacks
def edit_verb(ctx, obj, name):
	"""
	Present a verb editing window for a verb on 'obj' called 'name',
	through the connection to user.
	"""
	security.check_allowed(ctx, 'edit_verb', obj)
	
	if not(ctx.is_connected_player(ctx)):
		raise errors.PermissionError, "A non-connected-player entity cannot edit a verb!"
	
	info = get_verb_details(ctx, obj, name)
	
	response = yield ctx._connection.open_editor('verb', info)
	if(response):
		set_verb_details(ctx, obj, name, response)

def get_verb_details(ctx, obj, name):
	info = {u'origin':unicode(obj)}
	verb = None
	
	if(obj.has_verb(ctx, name)):
		verb = obj._vdict[name]
		if not(verb.is_readable(ctx)):
			raise errors.PermissionError, "The verb '" + name + "' is not readable to you."
		
		info[u'names'] = verb.get_names(ctx)
		info[u'code'] = unicode(verb.get_code(ctx))
		info[u'owner'] = unicode(verb.get_owner(ctx))
	else:
		info[u'names'] = [name]
		info[u'code'] = u''
		info[u'owner'] = unicode(ctx)
	
	return info

def set_verb_details(ctx, obj, name, info):
	if(obj.has_verb(ctx, name)):
		verb = obj._vdict[name]
		obj.remove_verb(ctx, name)
		def preset_verb_acl(new_verb):
			new_verb._vitals[u'acl'] = verb._vitals[u'acl']
		acl_func = preset_verb_acl
	else:
		acl_func = security.default_verb_acl
	
	owner = obj.get_registry(Q).get(info[u'owner'])
	obj.add_verb(ctx, info[u'code'], info[u'names'], owner=owner, acl_config=acl_func)

@inlineCallbacks
def edit_property(ctx, obj, name):
	"""
	Present a prop editing window for a prop on 'obj' called 'name',
	through the connection to user.
	"""
	security.check_allowed(ctx, 'edit_prop', obj)

	if not(ctx.is_connected_player(ctx)):
		raise errors.PermissionError, "A non-connected-player entity cannot edit a property!"
	
	info = get_property_details(ctx, obj, name)
	
	response = yield ctx._connection.open_editor('prop', info)
	
	if(response):
		set_property_details(ctx, obj, name, response)

def get_property_details(ctx, obj, name):
	from txspace.prop import EVAL_DYNAMIC_CODE, EVAL_STRING, EVAL_PYTHON
	
	info = {u'origin':unicode(obj), u'name':name}
	prop = None
	
	if(obj.has_property(ctx, name)):
		prop = obj._vdict[name]
		if not(prop.is_readable(ctx)):
			raise errors.PermissionError, "The verb '" + name + "' is not readable to you."
		info[u'eval_type'] = prop.get_eval_type(ctx)
		if(info[u'eval_type'] in (EVAL_DYNAMIC_CODE, EVAL_PYTHON)):
			info[u'value'] = prop.get_code(ctx)
		elif(info[u'eval_type'] == EVAL_STRING):
			info[u'value'] = prop.get_value(ctx)
		info[u'owner'] = unicode(prop.get_owner(ctx))
	else:
		info[u'eval_type'] = EVAL_STRING
		info[u'value'] = u""
		info[u'owner'] = unicode(ctx)
	
	return info

def set_property_details(ctx, obj, name, info):
	from txspace.prop import EVAL_PYTHON
	
	if(info[u'eval_type'] == EVAL_PYTHON):
		info[u'value'] = code.r_eval(ctx, info[u'value'])
	
	if(obj.has_property(ctx, name)):
		prop = obj._vdict[name]
		def preset_prop_acl(new_prop):
			new_prop._vitals[u'acl'] = prop._vitals[u'acl']
		obj.remove_property(ctx, info[u'name'])
		acl_config = preset_prop_acl
	else:
		acl_config = security.default_property_acl
	
	owner = obj.get_registry(Q).get(info[u'owner'])
	obj.add_property(ctx, info[u'name'], info[u'value'], owner=owner, eval_type=info[u'eval_type'], acl_config=acl_config)

@inlineCallbacks
def edit_acl(ctx, thing):
	"""
	Present an ACL editing window for 'thing', which may be an entity, verb, or property.
	"""
	from txspace import auth
	security.check_allowed(ctx, 'edit_acl', thing)
	
	if not(ctx.is_connected_player(ctx)):
		raise errors.PermissionError, "A non-connected-player entity cannot edit an ACL!"
	
	info = get_acl_details(ctx, thing)
	
	response = yield ctx._connection.open_editor('acl', info)
	if(response):
		set_acl_details(ctx, thing, response)

def get_acl_details(ctx, thing):
	return {u'permissions':copy.copy(thing._vitals[u'acl'])}

def set_acl_details(ctx, thing, info):
	thing._vitals[u'acl'] = []
	for permission in info[u'permissions']:
		if(permission[0] == u'allow'):
			security.allow(permission[1], permission[2], thing)
		elif(permission[0] == u'deny'):
			security.deny(permission[1], permission[2], thing)
