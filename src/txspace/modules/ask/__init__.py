# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Client-side prompt support.
"""

import simplejson

from zope.interface import classProvides

from twisted import plugin

from nevow import athena

from txspace import modules

def ask(p, question, callback, *args, **kwargs):
	details = dict(
		question	= question,
	)
	p.exchange.queue.send(p.caller.get_id(), dict(
		command		= 'ask',
		details		= details,
		object_id	= callback.get_origin().get_id(),
		method_name	= callback.get_names()[0],
		args		= args,
		kwargs		= kwargs,
	))

class AskModule(object):
	classProvides(plugin.IPlugin, modules.IModule)
	
	name = u'ask'
	script_url = u'/plugin/ask/assets/js/ask-plugin.js'
	
	def get_environment(self, p):
		return dict(
			ask = ask,
		)
	
	def get_resource(self, user):
		from txspace.modules.ask import resource
		return resource.AskDelegatePage()
	
	def handle_message(self, data, client):
		from txspace.modules.ask import transactions
		def _cb_ask(result):
			transactions.AnswerQuestion.run(
				transaction_child	= transactions.AskTransactionChild,
				user_id		= client.user_id,
				object_id	= data['object_id'],
				method_name	= data['method_name'].encode('utf8'),
				response	= result.encode('utf8'),
				args		= simplejson.dumps(data['args']),
				kwargs		= simplejson.dumps(data['kwargs']),
			)
		d = client.callRemote('plugin', self.name, self.script_url, data['details'])
		d.addCallback(_cb_ask)
	
	def activate_athena_commands(self, child):
		pass



