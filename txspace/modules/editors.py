# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Graphical object editor support.
"""

import os.path

from zope.interface import classProvides

import simplejson

from twisted import plugin
from twisted.internet import defer
from twisted.protocols import amp

from nevow import loaders, rend, athena

from txspace import assets, client, code, modules, transact, parser

def responder(cls):
	def _responder(func):
		func.respondsTo = cls
		return func
	return _responder

def edit(p, item):
	p.exchange.queue.send(p.caller.get_id(), dict(
		command		= 'editor',
		details		= item.get_details(),
	))

def access(p, item):
	acl = p.exchange.get_access(item.get_id(), item.get_type())
	details = dict(
		id		= str(item),
		type	= item.get_type(),
		origin	= str(getattr(item, 'origin', '')),
		access	= [dict(
			access_id	= rule['id'],
			rule		= rule['rule'],
			access		= rule['type'],
			accessor	= str(p.exchange.get_object(rule['accessor_id'])) if rule['accessor_id'] else rule['group'],
			permission	= rule['permission_name'],
		) for rule in acl]
	)
	
	p.exchange.queue.send(p.caller.get_id(), dict(
		command			= 'access',
		details			= details,
	))

class EditorDelegatePage(rend.Page):
	def __init__(self, user):
		self.user = user
	
	def locateChild(self, ctx, segments):
		if(segments and self.user and segments[0] in ('object', 'verb', 'property', 'access')):
			template = assets.get_template_path(segments[0] + '-editor')
			className = ''.join([x.capitalize() for x in os.path.basename(template).split('-')])
			cls = type(className, (rend.Page,), dict(
				docFactory	= loaders.xmlfile(template),
				user		= self.user
			))
			return (cls(), segments[2:])
		
		return super(rend.Page, self).locateChild(ctx, segments)

class AccessEditorModule(object):
	classProvides(plugin.IPlugin, modules.IModule)
	
	name = u'access'
	script_url = u'/assets/js/editor-plugin.js'
	
	def get_environment(self, p):
		return dict(
			access			= access,
		)
	
	def get_resource(self, user):
		return EditorDelegatePage(user)
	
	def handle_message(self, data, client):
		def _cb_accessedit(result):
			return ModifyAccess.run(
				transaction_child	= EditorTransactionChild,
				user_id		= client.user_id,
				object_id	= str(data['details']['id']),
				type		= data['details']['type'].encode('utf8'),
				access		= [dict(
					access_id	= int(access_id),
					deleted		= item['deleted'],
					rule		= item['rule'].encode('utf8'),
					access		= item['access'].encode('utf8'),
					accessor	= item['accessor'].encode('utf8'),
					permission	= item['permission'].encode('utf8'),
					weight		= item['weight'],
				) for access_id, item in result['access'].items()]
			) if result else None
		d = client.callRemote('plugin', self.name, self.script_url, data['details'])
		d.addCallback(_cb_accessedit)
	
	def activate_athena_commands(self, child):
		pass

class EditorModule(object):
	classProvides(plugin.IPlugin, modules.IModule)
	
	name = u'editor'
	script_url = u'/assets/js/editor-plugin.js'
	
	def get_environment(self, p):
		return dict(
			edit			= edit,
		)
	
	def get_resource(self, user):
		return EditorDelegatePage(user)
	
	def handle_message(self, data, client):
		if(data['details']['kind'] == 'object'):
			def _cb_objedit(result):
				return ModifyObject.run(
					transaction_child	= EditorTransactionChild,
					user_id		= client.user_id,
					object_id	= data['details']['id'],
					name		= result['name'].encode('utf8'),
					location	= result['location'].encode('utf8'),
					parents		= result['parents'].encode('utf8'),
					owner		= result['owner'].encode('utf8'),
				) if result else None
			d = client.callRemote('plugin', self.name, self.script_url, data['details'])
			d.addCallback(_cb_objedit)
		elif(data['details']['kind'] == 'property'):
			def _cb_propedit(result):
				return ModifyProperty.run(
					transaction_child	= EditorTransactionChild,
					user_id		= client.user_id,
					object_id	= data['details']['origin'].encode('utf8'),
					property_id	= str(data['details']['id']),
					name		= result['name'].encode('utf8'),
					value		= result['value'].encode('utf8'),
					type		= str(result['type']),
					owner		= result['owner'].encode('utf8'),
				) if result else None
			d = client.callRemote('plugin', self.name, self.script_url, data['details'])
			d.addCallback(_cb_propedit)
		elif(data['details']['kind'] == 'verb'):
			def _cb_verbedit(result):
				return ModifyVerb.run(
					transaction_child	= EditorTransactionChild,
					user_id		= client.user_id,
					object_id	= data['details']['origin'].encode('utf8'),
					verb_id		= str(data['details']['id']),
					names		= result['names'].encode('utf8'),
					code		= result['code'].encode('utf8'),
					exec_type	= result['exec_type'].encode('utf8'),
					owner		= result['owner'].encode('utf8'),
				) if result else None
			d = client.callRemote('plugin', self.name, self.script_url, data['details'])
			d.addCallback(_cb_verbedit)
		return d
	
	def activate_athena_commands(self, child):
		for name, value in EditorRemoteReference.__dict__.items():
			if(callable(value)):
				setattr(child.__class__, name, athena.expose(value))

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
					if(type == 'verb'):
						item.add_name(name)
			caller = x.get_object(user_id)
			p = parser.TransactionParser(parser.Lexer(''), caller, x)
			edit(p, item)
		
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
			access(p, item)
		
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
			p.set_value(value, type=type)
		
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
			return obj.get_details()

class EditorRemoteReference(object):
	def req_object_editor(self, object_id):
		"""
		Open an object editor as requested by the client.
		"""
		return OpenEditor.run(
			transaction_child	= EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= 'object',
			name		= '',
		)
	
	def req_verb_editor(self, object_id, verb_name):
		"""
		Open a verb editor as requested by the client.
		"""
		return OpenEditor.run(
			transaction_child	= EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= 'verb',
			name		= verb_name.encode('utf8'),
		)
	
	def req_property_editor(self, object_id, property_name):
		"""
		Open a property editor as requested by the client.
		"""
		return OpenEditor.run(
			transaction_child	= EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= 'property',
			name		= property_name.encode('utf8'),
		)
	
	def req_access_editor(self, object_id, type, name):
		"""
		Open an access editor as requested by the client.
		"""
		return OpenAccess.run(
			transaction_child	= EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= type.encode('utf8'),
			name		= name.encode('utf8'),
		)
	
	@defer.inlineCallbacks
	def get_object_details(self, object_id):
		"""
		Return object details (id, attributes, verbs, properties).
		"""
		result = yield GetObjectDetails.run(
			transaction_child	= EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
		)
		result = simplejson.loads(simplejson.dumps(result).decode('utf8'))
		defer.returnValue(result)
	
	def remove_verb(self, object_id, verb_name):
		"""
		Attempt to remove a verb from an object.
		"""
		return RemoveVerb.run(
			transaction_child	= EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			verb_name	= verb_name.encode('utf8'),
		)
	
	def remove_property(self, object_id, property_name):
		"""
		Attempt to remove a property from an object.
		"""
		return RemoveProperty.run(
			transaction_child	= EditorTransactionChild,
			user_id			= self.user_id,
			object_id		= unicode(object_id).encode('utf8'),
			property_name	= property_name.encode('utf8'),
		)

