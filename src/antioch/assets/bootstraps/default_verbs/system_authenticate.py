#!/usr/bin/python

# InnerSpace
# Copyright (C) 1999-2006 Phil Christensen
#
# $Id: sys_authenticate.py 184 2007-03-04 18:54:05Z phil $
#
# See LICENSE for details

username = args[0]
password = args[1]

if(username == 'guest'):
	owner = system.get_property('default_owner')
	classroom = get_obj("The Classroom")
	class_player = get_obj('class_player')
	
	# get the list of available guest names, which
	# also sets the total number of possible guests
	if(system.has_readable_property('guest_names')):
		guest_names = system.get_property('guest_names')
	else:
		guest_names = ['Red Guest', 'Blue Guest', 'Yellow Guest',
						'Green Guest', 'Orange Guest', 'Purple Guest']
	
	# get the registry where we keep the guest objects
	if(system.has_readable_property('guestbook')):
		guestbook = system.get_property('guestbook')
	else:
		guestbook = {}
		system.add_property('guestbook', guestbook, owner)
	
	# the first time, we will create guest objects
	# for all guest names
	guest = None
	for name in guest_names:
		if(name in guestbook):
			if(not guest and not guestbook[name].is_connected_player()):
				guest = guestbook[name]
				guest_name = name
		elif(not count_names(name)):
			guest_object = new_obj(name, True)
			guest_object.set_location(classroom)
			guest_object.set_player()
			guest_object.set_parent(class_player)
			guest_object.set_owner(guest_object)
			if(not guest):
				guest = guest_object
				guest_name = name
				
	
	if(not guest):
		print "[guests] rejected, too many guests"
		return "Sorry, there are too many guests already."
	
	guestbook[guest_name] = guest
	
	return guest
	
return None