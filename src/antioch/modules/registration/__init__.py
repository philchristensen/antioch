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

from antioch import modules, errors

from antioch.modules.registration import transactions, resource

VERSION = 2

def request_account(p, name, email):
	current_version = p.exchange.get_property(1, 'registration-version')
	if(not current_version or current_version.value < VERSION):
		transactions.UpdateSchema.run(
			transaction_child	= transactions.RegistrationTransactionChild,
		)
		# p.exchange.queue.push(p.caller.get_id(), dict(
		# 	plugin			= 'registration',
		# 	command			= 'update-schema',
		# ))
	
	transactions.RequestAccount.run(
		transaction_child	= transactions.RegistrationTransactionChild,
		name				= data['details']['name'].encode('utf8'),
		email				= data['details']['email'].encode('utf8'),
	)
	# p.exchange.queue.push(p.caller.get_id(), dict(
	# 	plugin			= 'registration',
	# 	command			= 'request-account',
	# 	details			= dict(
	# 		name	= name,
	# 		email	= email,
	# 	),
	# ))

def change_caller_password(p):
	p.exchange.queue.push(p.caller.get_id(), dict(
		plugin			= 'registration',
		command			= 'change-password',
	))

class RegistrationModule(object):
	classProvides(plugin.IPlugin, modules.IModule)
	
	name = u'registration'
	script_url = u'/plugin/registration/assets/js/registration-plugin.js'
	
	def get_commands(self):
		from antioch.modules.registration import transactions
		from antioch.modules import discover_commands
		return discover_commands(transactions)
	
	def get_resource(self, user):
		return resource.RegistrationPage(user)
	
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
		elif(data['command'] == 'change-password'):
			client.callRemote('plugin', self.name, self.script_url, {u'kind':u'change-password'})
	
	def get_environment(self):
		return dict(
			request_account			= request_account,
			change_caller_password	= change_caller_password,
		)
