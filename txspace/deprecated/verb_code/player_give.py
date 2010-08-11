# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

if not(has_dobj()):
	caller.write("What do you want to %s?" % words[0], is_error=True)
	return

thing = get_dobj()

your = dobj_spec_str
if(your == 'my'):
	your = 'your '
elif(your):
	your += ' '

if(words[0] == 'give'):
	if not(has_pobj('to')):
		caller.write("Who do you want to give %s%s to?" % (your, thing), is_error=True)
		return
	destination = get_pobj("to")
	if not(destination.is_player()):
		caller.write("%s can't take %s%s" % (destination, your, thing), is_error=True)
	thing.set_location(destination)
	caller.write("You gave %s %s%s" % (destination, your, thing))
	return

if(words[0] == 'put'):
	if not(has_pobj('in') or has_pobj('on')):
		caller.write("Where do you want to put %s%s?" % (your, thing))
		return
	if(has_pobj('in')):
		destination = get_pobj('in')
		if(destination.is_player()):
			caller.write("You can't %s %s%s into %s" % (words[0], your, thing, destination), is_error=True)
			return
		prep = 'into'
		thing.set_location(destination)
	else:
		destination = get_pobj('on')
		if(destination.is_player()):
			caller.write("You can't %s %s%s onto %s" % (words[0], your, thing, destination), is_error=True)
			return
		prep = 'onto'
		thing.set_location(destination)
elif(words[0] == 'drop' and len(prepositions) == 0):
	destination = caller.get_location()
	thing.set_location(destination)
	prep = 'in'
else:
	caller.write("I don't know how to %s something that way." % words[0])
	return

caller.write('You %s %s%s %s %s' %(words[0], your, thing, prep, destination))
