# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

from __future__ import absolute_import

import logging

from celery import shared_task

from antioch.util import json
from antioch.core import parser, tasks

log = logging.getLogger(__name__)

@shared_task
def openeditor(user_id, object_id, type, name):
	with tasks.get_exchange(user_id) as x:
		if(type == 'object'):
			item = x.get_object(object_id)
		else:
			item = getattr(x, 'get_' + type)(object_id, name)
			if(item is None):
				item = x.instantiate(type, owner_id=user_id, origin_id=object_id, name=name)
		caller = x.get_object(user_id)
		p = parser.TransactionParser(parser.Lexer(''), caller, x)
		from antioch.plugins import editors
		editors.edit(p, item)
	
	return {'response': True}

@shared_task
def openaccess(user_id, object_id, type, name):
	with tasks.get_exchange(user_id) as x:
		origin = x.get_object(object_id)
		caller = x.get_object(user_id)
		if(type == 'object'):
			item = origin
		else:
			item = getattr(origin, 'get_' + type)(name)
		
		p = parser.TransactionParser(parser.Lexer(''), caller, x)
		from antioch.plugins import editors
		editors.access(p, item)
	
	return {'response': True}

@shared_task
def modifyobject(user_id, object_id, name, location, parents, owner):
	with tasks.get_exchange(user_id) as x:
		o = x.get_object(object_id)
		o.set_name(name, real=True)
		o.set_location(x.get_object(location))
		o.set_owner(x.get_object(owner))
		
		old_parents = o.get_parents()
		new_parents = [x.get_object(p.strip()) for p in parents.split(',') if p.strip()]
		
		[o.remove_parent(p) for p in old_parents if p not in new_parents]
		[o.add_parent(p) for p in new_parents if p not in old_parents]
	
	return {'response': True}

@shared_task
def modifyverb(user_id, object_id, verb_id, names, code, ability, method, owner):
	with tasks.get_exchange(user_id) as x:
		names = [n.strip() for n in names.split(',')]
		
		v = x.load('verb', verb_id)
		v.set_names(names)
		v.set_owner(x.get_object(owner))
		v.set_code(code)
		
		v.set_ability(ability)
		v.set_method(method)
	
	return {'response': True}

@shared_task
def removeverb(user_id, object_id, verb_name):
	with tasks.get_exchange(user_id) as x:
		obj = x.get_object(object_id)
		obj.remove_verb(verb_name)
	
	return {'response': True}

@shared_task
def removeproperty(user_id, object_id, property_name):
	with tasks.get_exchange(user_id) as x:
		obj = x.get_object(object_id)
		obj.remove_property(property_name)
	
	return {'response': True}

@shared_task
def modifyproperty(user_id, object_id, property_id, name, value, type, owner):
	with tasks.get_exchange(user_id) as x:
		p = x.load('property', property_id)
		p.set_name(name)
		p.set_owner(x.get_object(owner))
		p.set_value(json.loads(value, exchange=x), type=type)
	
	return {'response': True}

@shared_task
def modifyaccess(user_id, object_id, type, access):
	with tasks.get_exchange(user_id) as x:
		subject = x.get_object(object_id)
		for rule in access:
			if(rule['access'] == 'accessor'):
				rule['accessor'] = x.get_object(rule['accessor'])
			x.update_access(subject=subject, **rule)

	return {'response': True}

@shared_task
def getobjectdetails(user_id, object_id):
	with tasks.get_exchange(user_id) as x:
		obj = x.get_object(object_id)
		details = obj.get_details()
	
	return details