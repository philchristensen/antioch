# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import hashlib

from twisted.protocols import amp

from antioch import transact, parser, json, sql, errors

from antioch.modules.registration import email

def send_registration_message(user):
	x = user.get_exchange()
	system = x.get_object(1)
	
	user_auth_code = None
	
	subject = 'Welcome to antioch!'
	content = """An antioch player was created for %(user)s at %(hostname)s. For
	account verification purposes, we ask you to confirm your email address by
	visiting the following link:

	    http://%(hostname)s/plugin/registration/confirm/%(auth_code)s

	If you believe you have received this message in error, please ignore this email.
	""" % dict(
		user		= user.get_name(),
		hostname	= system.get('hostname', hostname).value,
		auth_code	= user_auth_code,
	)
	
	email.send_user_message(x.get_object(1), user, subject, content)

class UpdateSchema(transact.WorldTransaction):
	arguments = []

class RequestAccount(transact.WorldTransaction):
	arguments = [
		('name', amp.String()),
		('email', amp.String()),
	]
	
	errors = {
		errors.AccessError : 'ACCESS_ERROR',
		errors.PermissionError : 'PERMISSION_ERROR',
		errors.AmbiguousObjectError : 'AMBIGUOUS_OBJECT_ERROR',
	}

class RegistrationTransactionChild(transact.TransactionChild):
	@UpdateSchema.responder
	def update_schema(self):
		with self.get_exchange() as x:
			try:
				x.pool.runQuery(sql.build_select('player', email='user@example.com', auth_code=None))
			except Exception, e:
				x.rollback()
				x.begin()
				x.pool.runOperation("ALTER TABLE player ADD COLUMN email varchar(255)")
				x.pool.runOperation("ALTER TABLE player ADD COLUMN auth_token varchar(255)")
				system = x.get_object(1)
				if('registration-version' not in system):
					system.add_property('registration-version')
				from antioch.modules import registration
				system['registration-version'].value = registration.VERSION
	
	@RequestAccount.responder
	def request_account(self, name, email):
		passwd = hashlib.md5(email).hexdigest()[:8]
		with self.get_exchange() as x:
			existing = x.get_object(name)
			if(existing):
				raise errors.AmbiguousObjectError(name, existing)
			
			hammer = x.get_object('wizard hammer')
			user = hammer.add_user(dict(
				name	= name,
				passwd	= passwd,
			))
			x.pool.runOperation(sql.build_update('player', 
									dict(email=email, auth_token=auth_token),
									dict(avatar_id=user.get_id())))
			
			send_registration_message(user)