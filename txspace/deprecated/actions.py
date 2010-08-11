# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Actions


The primary client actions are handled here. This controller
originally could tell the difference between web and pb clients,
and do the right thing where appropriate, but I've since abandoned
pb support (again).
"""

import traceback

from twisted.python import log

from txspace import parser, code, auth, errors
from txspace.security import Q

def parse(user, registry, command):
	try:
		log.msg('%s (%r): %s' % (user, getattr(user, '_connection', None), command))
		#parse the sentence
		p = parser.Parser(parser.Lexer(command), user, registry)
		#get the verb
		verb = p.get_verb()
		#if we got this far, we're good to go, so execute the verb
		verb.execute(user, code.get_environment(user, verb, p))
	except errors.UserError, e:
		user.write(user, str(e), is_error=True)
	except errors.TestError, e:
		raise e
	except Exception, e:
		trace = traceback.format_exc()
		user.write(user, trace, is_error=True)

def handle_login(user, mind):
	if(mind and hasattr(mind, 'remote_host')):
		system = user.get_registry(Q).get(0)
		if(system.has_verb(Q, 'connect') and not system.call_verb(Q, 'connect', mind.remote_host)):
			raise NotImplementedError("permission denied")
	
	log.msg(user, "logged in")
	if(system.has_callable_verb(Q, "login")):
		system.call_verb(Q, "login", user)
	
	user.set_observing(Q, user.get_location(Q))

def handle_logout(user):
	log.msg(user, "logged out")
	system = user.get_registry(Q).get(0)
	if(system.has_callable_verb(Q, "logout")):
		system.call_verb(Q, "logout", user_obj)

