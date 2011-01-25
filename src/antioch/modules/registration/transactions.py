# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import hashlib, socket

from twisted.protocols import amp

from antioch import transact, parser, json, sql, errors, session

from antioch.modules.registration import mailer

def send_registration_message(user, auth_token):
	x = user.get_exchange()
	system = x.get_object(1)
	hostname = socket.gethostname()
	
	subject = 'Welcome to antioch!'
	content = """An antioch player was created for %(user)s at %(hostname)s. For
	account verification purposes, we ask you to confirm your email address by
	visiting the following link:

	    http://%(hostname)s/plugin/registration/reset-password/%(auth_token)s

	If you believe you have received this message in error, please ignore this email.
	""" % dict(
		user		= user.get_name(),
		hostname	= system.get('hostname', hostname).value,
		auth_token	= auth_token,
	)
	
	mailer.send_user_message(x.get_object(1), user, subject, content)

class UpdateSchema(transact.WorldTransaction):
	arguments = []
	
	response = [
		('result', amp.Boolean()),
	]

class RequestAccount(transact.WorldTransaction):
	arguments = [
		('name', amp.String()),
		('email', amp.String()),
	]
	
	response = [
		('result', amp.Boolean()),
	]
	
	errors = {
		errors.AccessError : 'ACCESS_ERROR',
		errors.PermissionError : 'PERMISSION_ERROR',
		errors.AmbiguousObjectError : 'AMBIGUOUS_OBJECT_ERROR',
	}

class ValidateAuthToken(transact.WorldTransaction):
	arguments = [
		('auth_token', amp.String()),
	]
	
	response = [
		('avatar_id', amp.Integer()),
	]
	
	errors = {
		errors.AccessError : 'ACCESS_ERROR',
		errors.PermissionError : 'PERMISSION_ERROR',
		errors.AmbiguousObjectError : 'AMBIGUOUS_OBJECT_ERROR',
		errors.NoSuchObjectError : 'NO_SUCH_OBJECT_ERROR',
	}

class ChangePassword(transact.WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('new_password', amp.String()),
		('old_password', amp.String(optional=True)),
	]
	
	response = [
		('result', amp.Boolean()),
	]

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
				if('registration_version' not in system):
					system.add_property('registration_version')
				from antioch.modules import registration
				system['registration_version'].value = registration.VERSION
		return dict(result=True)
	
	@RequestAccount.responder
	def request_account(self, name, email):
		passwd = session.createSessionCookie()[:8]
		auth_token = session.createSessionCookie()
		with self.get_exchange() as x:
			existing = x.get_object(name, return_list=True)
			if(existing):
				raise errors.AmbiguousObjectError(name, existing)
			
			hammer = x.get_object('wizard hammer')
			user = hammer.add_user(dict(
				name		= name,
				passwd		= passwd,
			))
			x.pool.runOperation(sql.build_update('player', 
									dict(email=email, auth_token=auth_token),
									dict(avatar_id=user.get_id())))
			
			send_registration_message(user, auth_token)
		return dict(result=True)
	
	@ValidateAuthToken.responder
	def validate_auth_token(self, auth_token):
		with self.get_exchange() as x:
			user = x.pool.runQuery(sql.build_select('player', auth_token=auth_token))
			if not(user):
				raise errors.NoSuchObjectError(auth_token)
			elif(len(user) > 1):
				raise errors.AmbiguousObjectError(message="Ambiguous auth token %s" % auth_token)
		return dict(avatar_id=user[0]['avatar_id'])
	
	@ChangePassword.responder
	def change_password(self, user_id, new_password, old_password=None):
		with self.get_exchange(user_id) as x:
			if(old_password and not x.validate_password(user_id, old_password)):
				raise errors.PermissionError("Current password is incorrect.")
			
			x.ctx.set_player(passwd=new_password)
		return dict(result=True)
