import simplejson

def loads(j, exchange=None):
	if not(j):
		return j
	
	def to_entity(d):
		if(len(d) != 1):
			return d
		key = d.keys()[0]
		if(key[0] == '#'):
			try:
				return exchange.get_object(key)
			except:
				return 'missing object %s' % key
		return d
	
	try:
		if(exchange):
			return simplejson.loads(j, object_hook=to_entity)
		else:
			return simplejson.loads(j)
	except simplejson.decoder.JSONDecodeError, e:
		return j
	
def dumps(obj):
	from antioch import model
	def from_entity(o):
		if not(isinstance(o, model.Object)):
			return o
		return {'#%d' % o.get_id():o.get_name(real=True)}
	
	return simplejson.dumps(obj, default=from_entity)
