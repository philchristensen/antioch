# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Online signup for new players.
"""

import logging

import pkg_resources as pkg

from zope.interface import classProvides

from twisted.protocols import amp

from antioch import IPlugin
from antioch.util import json
from antioch.core import transact, parser, code

log = logging.getLogger(__name__)

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

class SignupTransactionChild(transact.TransactionChild):
	@AddPlayer.responder
	def add_player(self, name, passwd, enabled=True):
		try:
			log.debug("Creating a player for %r" % name)
			with self.get_exchange() as x:
				user = code.run_system_verb(x, 'add_player', name, passwd, enabled)
		
			return dict(avatar_id=user.id)
		except Exception, e:
			log.error(e)
	
	@EnablePlayer.responder
	def enable_player(self, player_id):
		with self.get_exchange() as x:
			code.run_system_verb(x, 'enable_player', x.get_object(player_id))
		
		return dict(result=True)

class SignupPlugin(object):
	classProvides(IPlugin)
	
	script_url = None
	transaction_child = SignupTransactionChild
	
	def initialize(self, exchange):
		p = 'antioch.plugins.signup.verbs'
		system = exchange.get_object(1)
		system.add_verb('add_player', **dict(
			method		= True,
			filename	= pkg.resource_filename(p, 'system_add_player.py')
		))
		
		system.add_verb('enable_player', **dict(
			method		= True,
			filename	= pkg.resource_filename(p, 'system_enable_player.py')
		))
	
	def get_environment(self):
		return dict(
			add_player		= self.add_player,
			enable_player	= self.enable_player,
		)
	
	def get_commands(self):
		return dict(
			addplayer		= AddPlayer,
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

