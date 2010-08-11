# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
This creates a minimal database of objects and verbs from a supplied,
presumed empty registrty object.

Other core packages may not require an empty database, and in fact, this
one would just add a number of objects and verbs to an existing registry,
but the use of a "used" registry is not reccomended.
"""
import os.path

from txspace import entity, security, prop
from txspace.security import Q

def init(registry, datadir):
	system_object = registry.get(0)
	
	class_wizard = registry.new(u"class_wizard", unique=True)
	class_programmer = registry.new(u"class_programmer", unique=True)
	class_author = registry.new(u"class_author", unique=True)
	class_player = registry.new(u"class_player", unique=True)
	class_room = registry.new(u"class_room", unique=True)
	class_door = registry.new(u"class_door", unique=True)
	
	security.allow('programmers', 'add_child', class_wizard)
	security.allow('programmers', 'add_child', class_programmer)
	security.allow('programmers', 'add_child', class_author)
	security.allow('programmers', 'add_child', class_player)
	security.allow('programmers', 'add_child', class_room)
	security.allow('programmers', 'add_child', class_door)
	

	wizard = registry.new(u"wizard", unique=True)
	phil = registry.new(u"phil", unique=True)

	mask = registry.new(u"mask")
	
	room = registry.new(u"The Laboratory")
	lobby = registry.new(u"The Lobby")
	
	class_wizard.set_location(Q, room)
	class_wizard.set_owner(Q, wizard)
	
	class_author.set_location(Q, room)
	class_author.set_owner(Q, wizard)
	
	class_player.set_location(Q, room)
	class_player.set_owner(Q, wizard)
	
	class_programmer.set_location(Q, room)
	class_programmer.set_owner(Q, wizard)
	
	class_room.set_location(Q, room)
	class_room.set_owner(Q, wizard)
	
	class_wizard.set_parent(Q, class_programmer)
	class_programmer.set_parent(Q, class_author)
	class_author.set_parent(Q, class_player)
	
	phil.set_player(Q)
	phil.set_location(Q, room)
	phil.add_property(Q, u'passwd', u'phil', owner=wizard)
	phil.set_owner(Q, phil)
	phil.set_parent(Q, class_author)
	
	wizard.set_wizard(Q)
	wizard.set_location(Q, room)
	wizard.add_property(Q, u'passwd', u'wizard', owner=wizard)
	wizard.set_owner(Q, wizard)
	wizard.set_parent(Q, class_wizard)
	security.allow(wizard, 'multi_login', wizard);

	mask.set_location(Q, room)
	
	room.set_parent(Q, class_room)
	lobby.set_parent(Q, class_room)
	
	wizard.add_property(Q, 
					  u'description',
					  u"""<p>Like many Wizards, this one has the appearance of an
							old man, albeit one who grew old slowly with the passage
							of the centuries. His hair is white, and his long white
							beard grows down below his waist. His eyebrows are
							particularly noticeable; they are so long and bushy
							that they stuck out from beneath the rim of his hat.</p>
							
							<p>He is dressed in a long grey cloak, and wears a tall
							shady-brimmed pointed blue hat, a silver scarf, and
							long black boots.</p>
							""".replace('\t', ''),
					  owner=wizard,
					  eval_type=prop.EVAL_STRING,
					  acl_config=security.readable_property_acl)
	
	room.add_property(Q, 
					  u'description',
					  u"""<p>The room you see before you is filled with clutter of every kind
						imaginable. A large workbench lines the length of the north wall,
						covered with teetering piles of seemingly useless junk.</p>
						
						<p>Throughout the room are a number of glowing objects. Some of them
						look like simple and obvious things, whereas others just seem to take
						the form of an orb, floating a few inches above the floor (or whatever
						surface they've been carelessly tossed upon).</p>
						""".replace('\t', ''),
					  owner=wizard,
					  eval_type=prop.EVAL_STRING,
					  acl_config=security.readable_property_acl)
	
	lobby.add_property(Q, 
					  u'description',
					  u"""<p>This small, cramped room is filled with uncomfortable chairs from
						one wall to another. Ancient periodicals cover the various endtables
						scattered throughout the room, but the thick layer of dust coating them
						suggests they haven't received much attention in awhile.</p>
						
						<p>In the east wall there's a small serivce window, next to a large
						digital counter under the words "NOW SERVING:" &emdash; but the digits
						appear to have been stuck on zero for some time.</p>
						""".replace('\t', ''),
					  owner=wizard,
					  eval_type=prop.EVAL_STRING,
					  acl_config=security.readable_property_acl)
	
	system_object.add_property(Q, 
							   u'default_player_class',
							   class_player,
							   owner=wizard,
							   acl_config=security.readable_property_acl)
	
	system_object.add_property(Q, 
							   u'default_room_class',
							   class_room,
							   owner=wizard,
							   acl_config=security.readable_property_acl)
	
	system_object.add_property(Q, 
							   u'default_owner',
							   wizard,
							   owner=wizard,
							   acl_config=security.readable_property_acl)
	
	registry.load_verb(class_room, os.path.join(datadir, 'room_get_observations.py'), [u'get_observations'], owner=class_wizard, is_method=True)
	
	registry.load_verb(system_object, os.path.join(datadir, 'sys_get_observations.py'), [u'get_observations'], owner=class_wizard, is_method=True)
	registry.load_verb(system_object, os.path.join(datadir, 'sys_connect.py'), [u'connect'], owner=class_wizard, is_method=True)
	registry.load_verb(system_object, os.path.join(datadir, 'sys_authenticate.py'), [u'authenticate'], owner=class_wizard, is_method=True)
	
	registry.load_verb(class_door, os.path.join(datadir, 'door_enter.py'), [u'enter'], owner=class_wizard, is_method=True)
	
	registry.load_verb(class_player, os.path.join(datadir, 'player_logout.py'), [u"@logout"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_player, os.path.join(datadir, 'player_look.py'), [u"look", u"inspect", u"examine"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_player, os.path.join(datadir, 'player_go.py'), [u"go"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_player, os.path.join(datadir, 'player_say.py'), [u"say"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_player, os.path.join(datadir, 'player_hear.py'), [u"hear"], owner=class_wizard, is_method=True)
	registry.load_verb(class_player, os.path.join(datadir, 'player_take.py'), [u'take', u'get', u'grab'], owner=class_wizard, is_ability=True)
	registry.load_verb(class_player, os.path.join(datadir, 'player_give.py'), [u'give', u'put', u'drop'], owner=class_wizard, is_ability=True)
	
	registry.load_verb(class_author, os.path.join(datadir, 'author_create.py'), [u"@create"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_author, os.path.join(datadir, 'author_dig.py'), [u"@dig"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_author, os.path.join(datadir, 'author_describe.py'), [u"@describe"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_author, os.path.join(datadir, 'author_tunnel.py'), [u"@tunnel"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_author, os.path.join(datadir, 'author_alias.py'), [u"@alias"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_author, os.path.join(datadir, 'author_alias-exit.py'), [u"@alias-exit"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_author, os.path.join(datadir, 'author_edit_prop.py'), [u"@prop"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_author, os.path.join(datadir, 'author_edit_obj.py'), [u"@edit"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_author, os.path.join(datadir, 'author_edit_acl.py'), [u"@acl"], owner=class_wizard, is_ability=True)
	
	registry.load_verb(class_programmer, os.path.join(datadir, 'programmer_exec.py'), [u"@exec"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_programmer, os.path.join(datadir, 'programmer_eval.py'), [u"@eval"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_programmer, os.path.join(datadir, 'programmer_edit_verb.py'), [u"@verb"], owner=class_wizard, is_ability=True)
	
	registry.load_verb(class_wizard, os.path.join(datadir, 'wizard_adduser.py'), [u"@adduser"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_wizard, os.path.join(datadir, 'wizard_parse.py'), [u"@parse"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_wizard, os.path.join(datadir, 'wizard_export.py'), [u"@export"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_wizard, os.path.join(datadir, 'wizard_load.py'), [u"@load"], owner=class_wizard, is_ability=True)
	registry.load_verb(class_wizard, os.path.join(datadir, 'wizard_reload.py'), [u"@reload"], owner=class_wizard, is_ability=True)
