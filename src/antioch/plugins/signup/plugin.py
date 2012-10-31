# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Online signup for new players.
"""

import pkg_resources as pkg

from zope.interface import classProvides

from twisted.protocols import amp

from antioch import IPlugin
from antioch.util import json
from antioch.core import transact, parser, code
from antioch.plugins.signup import transactions 

class AddPlayer(transact.WorldTransaction):
	arguments = [
		('name', amp.String()),
		('passwd', amp.String()),
		('enabled', amp.Boolean()),
	]
	response = [
		('avatar_id', amp.Integer()),
	]

class EnablePlayer(transact.WorldTransaction):
	arguments = [
		('player_id', amp.Integer()),
	]
	response = [('response', amp.Boolean())]

class SignupPlugin(object):
	classProvides(IPlugin)
	
	script_url = None
	
	def initialize(self, exchange):
		from antioch.plugins.signup import verbs
		
		system = exchange.get_object(1)
		system.add_verb('add_player', **dict(
			method		= True,
			filename	= pkg.resource_filename(verbs, 'system_add_player.py')
		))
	
	def get_environment(self):
		return dict(
			add_player		= self.add_player,
			enable_player	= self.enable_player,
		)
	
	def get_commands(self):
		return dict(
			addplayer		= AddUser,
			enableplayer	= EnablePlayer,
		)
	
	def add_player(self, p, name=None, passwd=None, enabled=True):
		system = p.exchange.get_object(1)
		p.caller.is_allowed('administer', system, fatal=True)
		klass = p.exchange.get_object('user class')
		user = p.exchange.instantiate('object', name=name, unique_name=True)
		user.set_owner(user)
		user.set_player(enabled, passwd=passwd)
		return user
	
	def enable_player(self, p, user):
		user.set_player(True)

class SignupTransactionChild(transact.TransactionChild):
	@AddPlayer.responder
	def add_player(self, name, email, passwd, enabled=True):
		with self.get_exchange() as x:
			user = code.run_system_verb('add_player', name, email, passwd, enabled)
		
		return dict(avatar_id=user.id)
	
	@EnablePlayer.responder
	def enable_player(self, player_id):
		with self.get_exchange() as x:
			code.run_system_verb('enable_player', x.get_object(player_id))
		
		return dict(result=True)


