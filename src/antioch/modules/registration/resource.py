# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import os.path

import pkg_resources as pkg

from twisted.internet import defer

from nevow import loaders, rend, inevow, tags

from antioch import assets, errors
from antioch.modules.registration import transactions

PAGE_CODES = ['reset-password', 'change-password']

class RegistrationPage(rend.Page):
	def __init__(self, user):
		self.user = user
		
		assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'webroot'))
		assets.enable_assets(self, assets_path)
	
	@defer.inlineCallbacks
	def locateChild(self, ctx, segments):
		if(segments):
			if(len(segments) == 2 and segments[0] == 'reset-password'):
				user = yield transactions.ValidateAuthToken.run(
					transaction_child	= transactions.RegistrationTransactionChild,
					auth_token			= segments[1],
				)
				result = (ResetPasswordPage(user), segments[2:])
			elif(self.user and segments[0] == 'change-password'):
				result = (ChangePasswordPage(self.user), segments[1:])
		
		if not(result):
			result = super(RegistrationPage, self).locateChild(ctx, segments)
		
		defer.returnValue(result)

class ResetPasswordPage(rend.Page):
	docFactory = loaders.xmlstr(pkg.resource_string('antioch.modules.registration', 'templates/reset-password.xml'))
	
	def __init__(self, user):
		self.user = user
		self.messages = []
	
	@defer.inlineCallbacks	
	def renderHTTP(self, ctx):
		request = inevow.IRequest(ctx)
		if(request.fields is not None):
			password = None
			verify = None
			if('password' in request.fields):
				password = request.fields['password'].value
			if('verify' in request.fields):
				verify = request.fields['verify'].value
			
			if(password == verify):
				try:
					result = yield transactions.ChangePassword.run(
						transaction_child	= transactions.RegistrationTransactionChild,
						user_id				= self.user['avatar_id'],
						new_password		= password,
					)
					if(result['result']):
						self.messages.append('Your password was changed.')
				except errors.PermissionError, e:
					self.messages.append(str(e))
			else:
				self.messages.append('Please enter your password twice to verify.')
		
		result = yield defer.maybeDeferred(super(ResetPasswordPage, self).renderHTTP, ctx)
		defer.returnValue(result)
	
	def render_messages(self, ctx, data):
		if not(self.messages):
			return ''
		return tags.ul()[[tags.li()[x] for x in self.messages]]

class ChangePasswordPage(rend.Page):
	docFactory = loaders.xmlstr(pkg.resource_string('antioch.modules.registration', 'templates/change-password.xml'))
	
	def __init__(self, user):
		self.user = user
		self.messages = []
	
	@defer.inlineCallbacks	
	def renderHTTP(self, ctx):
		request = inevow.IRequest(ctx)
		if(request.fields is not None):
			password = None
			verify = None
			if('original' in request.fields):
				original = request.fields['original'].value
			if('password' in request.fields):
				password = request.fields['password'].value
			if('verify' in request.fields):
				verify = request.fields['verify'].value
			
			if(password == verify):
				try:
					result = yield transactions.ChangePassword.run(
						transaction_child	= transactions.RegistrationTransactionChild,
						user_id				= self.user['avatar_id'],
						new_password		= password,
						old_password		= original,
					)
					if(result['result']):
						self.messages.append('Your password was changed.')
				except errors.PermissionError, e:
					self.messages.append(str(e))
			else:
				self.messages.append('Please enter your password twice to verify.')
		
		result = yield defer.maybeDeferred(super(ChangePasswordPage, self).renderHTTP, ctx)
		defer.returnValue(result)
	
	def render_messages(self, ctx, data):
		if not(self.messages):
			return ''
		return tags.ul()[[tags.li()[x] for x in self.messages]]
