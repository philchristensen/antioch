# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

from twisted.protocols import amp

from antioch.util import json
from antioch.core import transact, parser

class GetObjectDetails(transact.WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
	]
	response = [
		('id', amp.Integer()),
		('name', amp.String()),
		('kind', amp.String()),
		('parents', amp.String()),
		('owner', amp.String()),
		('location', amp.String()),
		('properties', amp.AmpList([
			('id', amp.Integer()),
			('name', amp.String()),
		])),
		('verbs', amp.AmpList([
			('id', amp.Integer()),
			('names', amp.String()),
		])),
	]

class OpenEditor(transact.WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('type', amp.String()),
		('name', amp.String()),
	]

class OpenAccess(transact.WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('type', amp.String()),
		('name', amp.String()),
	]

class ModifyObject(transact.WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.Integer()),
		('name', amp.String()),
		('location', amp.String()),
		('parents', amp.String()),
		('owner', amp.String()),
	]

class ModifyVerb(transact.WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('verb_id', amp.String()),
		('names', amp.String()),
		('code', amp.String()),
		('exec_type', amp.String()),
		('owner', amp.String()),
	]

class ModifyProperty(transact.WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('property_id', amp.String()),
		('name', amp.String()),
		('value', amp.String()),
		('type', amp.String()),
		('owner', amp.String()),
	]

class ModifyAccess(transact.WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('type', amp.String()),
		('access', amp.AmpList([
			('access_id', amp.Integer()),
			('deleted', amp.Boolean()),
			('rule', amp.String()),
			('access', amp.String()),
			('accessor', amp.String()),
			('permission', amp.String()),
			('weight', amp.Integer()),
		])),
	]

class RemoveVerb(transact.WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('verb_name', amp.String()),
	]

class RemoveProperty(transact.WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.String()),
		('property_name', amp.String()),
	]

class EditorTransactionChild(transact.TransactionChild):
	@OpenEditor.responder
	def open_editor(self, user_id, object_id, type, name):
		with self.get_exchange(user_id) as x:
			if(type == 'object'):
				item = x.get_object(object_id)
			else:
				item = getattr(x, 'get_' + type)(object_id, name)
				if(item is None):
					item = x.instantiate(type, owner_id=user_id, origin_id=object_id, name=name)
			caller = x.get_object(user_id)
			p = parser.TransactionParser(parser.Lexer(''), caller, x)
			from antioch.modules import editors
			editors.edit(p, item)
		
		return {'response': True}
	
	@OpenAccess.responder
	def open_access(self, user_id, object_id, type, name):
		with self.get_exchange(user_id) as x:
			origin = x.get_object(object_id)
			caller = x.get_object(user_id)
			if(type == 'object'):
				item = origin
			else:
				item = getattr(origin, 'get_' + type)(name)
			
			p = parser.TransactionParser(parser.Lexer(''), caller, x)
			from antioch.modules import editors
			editors.access(p, item)
		
		return {'response': True}
	
	@ModifyObject.responder
	def modify_object(self, user_id, object_id, name, location, parents, owner):
		with self.get_exchange(user_id) as x:
			o = x.get_object(object_id)
			o.set_name(name, real=True)
			o.set_location(x.get_object(location))
			o.set_owner(x.get_object(owner))
			
			old_parents = o.get_parents()
			new_parents = [x.get_object(p.strip()) for p in parents.split(',') if p.strip()]
			
			[o.remove_parent(p) for p in old_parents if p not in new_parents]
			[o.add_parent(p) for p in new_parents if p not in old_parents]
		
		return {'response': True}
	
	@ModifyVerb.responder
	def modify_verb(self, user_id, object_id, verb_id, names, code, exec_type, owner):
		with self.get_exchange(user_id) as x:
			names = [n.strip() for n in names.split(',')]
			
			v = x.load('verb', verb_id)
			v.set_names(names)
			v.set_owner(x.get_object(owner))
			v.set_code(code)
			
			if(exec_type == 'ability'):
				v.set_ability(True)
				v.set_method(False)
			elif(exec_type == 'method'):
				v.set_ability(False)
				v.set_method(True)
			else:
				v.set_ability(False)
				v.set_method(False)
		
		return {'response': True}
	
	@RemoveVerb.responder
	def remove_verb(self, user_id, object_id, verb_name):
		with self.get_exchange(user_id) as x:
			obj = x.get_object(object_id)
			obj.remove_verb(verb_name)
		
		return {'response': True}
	
	@RemoveProperty.responder
	def remove_property(self, user_id, object_id, property_name):
		with self.get_exchange(user_id) as x:
			obj = x.get_object(object_id)
			obj.remove_property(property_name)
		
		return {'response': True}
	
	@ModifyProperty.responder
	def modify_property(self, user_id, object_id, property_id, name, value, type, owner):
		with self.get_exchange(user_id) as x:
			p = x.load('property', property_id)
			p.set_name(name)
			p.set_owner(x.get_object(owner))
			p.set_value(json.loads(value, exchange=x), type=type)
		
		return {'response': True}
	
	@ModifyAccess.responder
	def modify_access(self, user_id, object_id, type, access):
		with self.get_exchange(user_id) as x:
			subject = x.get_object(object_id)
			for rule in access:
				if(rule['access'] == 'accessor'):
					rule['accessor'] = x.get_object(rule['accessor'])
				x.update_access(subject=subject, **rule)
	
		return {'response': True}
	
	@GetObjectDetails.responder
	def get_object_details(self, user_id, object_id):
		with self.get_exchange(user_id) as x:
			obj = x.get_object(object_id)
			details = obj.get_details()
		
		return details