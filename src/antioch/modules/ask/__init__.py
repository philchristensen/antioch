# antioch
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

from antioch import modules, transact

def ask(p, question, callback, *args, **kwargs):
	details = dict(
		question	= question,
	)
	p.exchange.queue.send(p.caller.get_id(), dict(
		command		= 'ask',
		details		= details,
		origin_id	= callback.get_origin().get_id(),
		verb_name	= callback.get_names()[0],
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
		from antioch.modules.ask import resource
		return resource.AskDelegatePage()
	
	def handle_message(self, data, client):
		def _cb_ask(result):
			transact.RegisterTask.run(
				user_id		= client.user_id,
				origin_id	= str(data['origin_id']),
				verb_name	= data['verb_name'].encode('utf8'),
				args		= simplejson.dumps(data['args'] + [result]),
				kwargs		= simplejson.dumps(data['kwargs']),
				delay		= 0,
			)
		d = client.callRemote('plugin', self.name, self.script_url, data['details'])
		d.addCallback(_cb_ask)
