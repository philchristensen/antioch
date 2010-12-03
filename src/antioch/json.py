import simplejson

def loads(j, exchange=None):
	if not(j):
		return j
	
	def to_entity(d):
		if('__object__' in d):
			try:
				return exchange.get_object(d['__object__'])
			except:
				return 'missing object #%(__object__)s' % d
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
		return {'__object__':o.get_id()}
	
	return simplejson.dumps(obj, default=from_entity)
