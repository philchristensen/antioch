# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

from __future__ import absolute_import

import logging

from celery import shared_task

from antioch import conf
from antioch.core import tasks, code

log = logging.getLogger(__name__)

@shared_task
def addplayer(name, passwd, enabled=True):
	log.debug("Creating a player for %r" % name)
	with tasks.get_exchange() as x:
		user = code.run_system_verb(x, 'add_player', name=name, passwd=passwd, enabled=enabled)

	return user.id

@shared_task
def enableplayer(player_id):
	with tasks.get_exchange() as x:
		code.run_system_verb(x, 'enable_player', x.get_object(x.get_avatar_id(player_id)))
	
	return dict(result=True)
