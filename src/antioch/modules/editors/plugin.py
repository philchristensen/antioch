# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Graphical object editor support.
"""

from zope.interface import classProvides

from twisted import plugin

from antioch import module
from antioch.core import transact

def edit(p, item):
	p.exchange.queue.push(p.caller.get_id(), dict(
		plugin		= 'editor',
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
	
	p.exchange.queue.push(p.caller.get_id(), dict(
		plugin			= 'access',
		details			= details,
	))

class EditorModule(object):
	classProvides(plugin.IPlugin, module.IModule)
	
	name = u'editors'
	script_url = u'/plugin/editor/assets/js/editor-plugin.js'
	
	def get_environment(self):
		return dict(
			edit			= edit,
			access			= access,
		)
	
	def get_resource(self, user):
		from antioch.modules.editors import resource
		return resource.EditorDelegatePage(user)
	
	def handle_message(self, data, client):
		from antioch.modules.editors import transactions
		if(data['details']['kind'] == 'object'):
			def _cb_objedit(result):
				return transactions.ModifyObject.run(
					transaction_child	= transactions.EditorTransactionChild,
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
				return transactions.ModifyProperty.run(
					transaction_child	= transactions.EditorTransactionChild,
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
				return transactions.ModifyVerb.run(
					transaction_child	= transactions.EditorTransactionChild,
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
		elif(data['details']['kind'] == 'access'):
			def _cb_accessedit(result):
				from antioch.modules.editors import transactions
				return transactions.ModifyAccess.run(
					transaction_child	= transactions.EditorTransactionChild,
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
		return d
	
	def get_commands(self):
		from antioch.modules.editors import transactions
		from antioch.modules import discover_commands
		return discover_commands(transactions)
	
	def activate_client_commands(self, child):
		from antioch.modules.editors.client import EditorRemoteReference
		from nevow import athena
		
		for name, value in EditorRemoteReference.__dict__.items():
			if(callable(value)):
				setattr(child.__class__, name, athena.expose(value))



