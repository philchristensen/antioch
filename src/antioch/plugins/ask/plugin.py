# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Client-side prompt support.
"""
from zope.interface import classProvides

from antioch import IPlugin

def ask(p, question, callback, *args, **kwargs):
	details = dict(
		question	= question,
	)
	p.exchange.queue.push(p.caller.get_id(), dict(
		command		= 'ask',
		details		= details,
		callback	= dict(
			origin_id	= callback.get_origin().get_id(),
			verb_name	= callback.get_names()[0],
			args		= args,
			kwargs		= kwargs,
		)
	))

class AskModule(object):
	classProvides(IPlugin)
	
	name = u'ask'
	script_url = u'/assets/js/ask-plugin.js'
	
	def get_environment(self):
		return dict(
			ask = ask,
		)
	
	def get_commands(self):
		return {}
	
