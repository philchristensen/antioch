# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Graphical object editor support.
"""

from zope.interface import classProvides

from antioch import conf, IPlugin
from antioch.core import transact

from antioch.plugins.editors.transactions import EditorTransactionChild

def edit(p, item):
	p.exchange.send_message(p.caller.get_id(), dict(
		command		= 'edit',
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
	
	p.exchange.send_message(p.caller.get_id(), dict(
		command			= 'access',
		details			= details,
	))

class EditorModule(object):
	classProvides(IPlugin)
	
	name = u'editor'
	script_url = u'%sjs/editor-plugin.js' % conf.get('static-url')
	transaction_child = EditorTransactionChild
	
	def get_environment(self):
		return dict(
			edit			= edit,
			access			= access,
		)
	
	def get_commands(self):
		from antioch.plugins.editors import transactions
		from antioch.plugins import discover_commands
		return discover_commands(transactions)

