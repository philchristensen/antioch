# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Default database bootstrap.
"""

from antioch import model, sql

for name in model.default_permissions:
	exchange.pool.runOperation(sql.build_insert('permission', name=name))

exchange.load_permissions()

system = exchange.instantiate('object', name='System Object')
set_default_permissions_verb = model.Verb(system)
set_default_permissions_verb._method = True
set_default_permissions_verb._code = """#!antioch
obj = args[0]
obj.allow('wizards', 'anything')
obj.allow('owners', 'anything')
obj.allow('everyone', 'read')
"""
exchange.save(set_default_permissions_verb)
set_default_permissions_verb.add_name('set_default_permissions')

wizard = exchange.instantiate('object', name='Wizard', unique_name=True)
wizard.set_owner(wizard)
system.set_owner(wizard)
set_default_permissions_verb.set_owner(wizard)

wizard.set_player(True, is_wizard=True, passwd='wizard')

user = exchange.instantiate('object', name='User', unique_name=True)
user.set_player(True, passwd='user')

room = exchange.instantiate('object', name="The Beginning")
room.set_owner(wizard)

user.set_location(room)
wizard.set_location(room)

exec_verb = exchange.instantiate('verb', dict(
	owner_id = wizard.get_id(),
	origin_id = wizard.get_id(),
	ability = True,
	method = False,
	code = """#!antioch
exec(command[6:])
""",
))
exec_verb.add_name('@exec')

eval_verb = exchange.instantiate('verb', dict(
	owner_id = wizard.get_id(),
	origin_id = wizard.get_id(),
	ability = True,
	method = False,
	code = """#!antioch
write(caller, eval(command[6:]))
""",
))
eval_verb.add_name('@eval')