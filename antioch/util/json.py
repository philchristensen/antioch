# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Encode/decode antioch JSON

antioch-flavored JSON contains object references, where objects are
saved in the format::

    {'o#1':'ObjectName'}
    {'v#1':'VerbName'}
    {'p#1':'PropertyName'}

These will be converted transparently by the dumps/loads functions
in this module.
"""

import json

def loads(j, exchange=None):
	"""
	Load some antioch-flavored JSON.
	
	If exchange is supplied, this will convert references to the real thing.
	"""
	if not(j):
		return j
	
	def to_entity(d):
		if(len(d) != 1):
			return d
		key = d.keys()[0]
		if(key[1] == '#'):
			try:
				if(key[0] == 'o'):
					return exchange.get_object(key[1:])
				elif(key[0] == 'v'):
					return exchange.instantiate('verb', id=int(key[2:]))
				elif(key[0] == 'p'):
					return exchange.instantiate('property', id=int(key[2:]))
			except:
				return 'missing:%s' % key
		return d
	
	try:
		if(exchange):
			return json.loads(j, object_hook=to_entity)
		else:
			return json.loads(j)
	except json.decoder.JSONDecodeError, e:
		return j.strip('"').strip("'")
	
def dumps(obj):
	"""
	Create some antioch-flavored JSON (containing antioch object references).
	"""
	from antioch.core import interface
	def from_entity(o):
		if not(isinstance(o, interface.Entity)):
			return o
		if(isinstance(o, interface.Object)):
			return {'o#%d' % o.get_id():o.get_name(real=True)}
		elif(isinstance(o, interface.Verb)):
			return {'v#%d' % o.get_id():o.name}
		elif(isinstance(o, interface.Property)):
			return {'p#%d' % o.get_id():o.name}
	
	return json.dumps(obj, default=from_entity)
