# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

from twisted.protocols import amp

from antioch import transact, parser, json, sql

class UpdateSchema(transact.WorldTransaction):
	arguments = []

class RequestAccount(transact.WorldTransaction):
	arguments = [
		('name', amp.String()),
		('email', amp.String()),
	]

class RegistrationTransactionChild(transact.TransactionChild):
	@UpdateSchema.responder
	def update_schema(self):
		with self.get_exchange() as x:
			try:
				x.pool.runQuery(sql.build_select('player', email='user@example.com'))
			except Exception, e:
				x.rollback()
				x.begin()
				x.pool.runOperation("ALTER TABLE player ADD COLUMN email varchar(255)")
				system = x.get_object(1)
				if('registration-version' not in system):
					system.add_property('registration-version')
				from antioch.modules import registration
				system['registration-version'].value = registration.VERSION
		return {'result':True}
