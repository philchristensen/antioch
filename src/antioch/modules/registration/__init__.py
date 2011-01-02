# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Graphical object editor support.
"""

from zope.interface import classProvides

from twisted import plugin

from antioch import modules, errors

from antioch.modules.registration import transactions

VERSION = 1

def request_account(p, name, email):
	current_version = p.exchange.get_property(1, 'registration-version')
	if(not current_version or current_version.value < VERSION):
		p.exchange.queue.send(p.caller.get_id(), dict(
			plugin			= 'registration',
			command			= 'update-schema',
		))
	
	p.exchange.queue.send(p.caller.get_id(), dict(
		plugin			= 'registration',
		command			= 'request-account',
		details			= dict(
			name	= name,
			email	= email,
		),
	))

class RegistrationModule(object):
	classProvides(plugin.IPlugin, modules.IModule)
	
	name = u'registration'
	
	def handle_message(self, data, client):
		if(data['command'] == 'update-schema'):
			transactions.UpdateSchema.run(
				transaction_child	= transactions.RegistrationTransactionChild,
			)
		elif(data['command'] == 'request-account'):
			transactions.RequestAccount.run(
				transaction_child	= transactions.RegistrationTransactionChild,
				name				= data['details']['name'].encode('utf8'),
				email				= data['details']['email'].encode('utf8'),
			)
	
	def get_environment(self):
		return dict(
			request_account			= request_account,
		)
