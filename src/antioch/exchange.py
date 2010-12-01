"""
the antioch ObjectExchange

essentially a replacement for the old Registry class, combined with
some new requirements needed by the DB persistence layer.

this is the connecting thread between the database and verb code
during a transaction. it is responsible for loading and saving objects,
verbs, properties and permissions, as well as caching objects loaded
during a single verb transaction.


permissions and properties/verbs

the only time an object's permissions are consulted is when we are adding
a verb or property. once it is added, any interactions with the verb or property
should examine those objects themselves. during deletion, both the object and the
attribute should be checked, for the following reason:


the owner of a property/verb should be able to delete something they own from
an object they don't (the only way that attribute could have been added in the
first place was because the object was writable to them).

however, the owner of the object should also have the ability to delete that
attribute. if so, then do they have rights to do other things (change properties,
edit verbs) simply because the attributes were defined on something they owned?

No, they don't. They can remove things they don't own from their object, but they cannot
change the value of those items.

"""
import crypt, string, random, time

from twisted.internet import defer
from twisted.python import util

from txamqp.client import Closed

from antioch import sql, model, errors

group_definitions = dict(
	owners		= lambda x,a,s: a.owns(s),
	wizards		= lambda x,a,s: x.is_wizard(a.get_id()),
	everyone	= lambda x,a,s: True,
)

salt = list(string.printable[:])

profile_exchange = False

def extract_id(literal):
	if(isinstance(literal, basestring) and literal.startswith('#')):
		end = literal.find("(")
		if(end == -1):
			end = literal.find( " ")
		if(end == -1):
			end = len(literal)
		return int(literal[1:end])
	
	if(isinstance(literal, (int, long))):
		return literal
	
	return None

class ObjectExchange(object):
	permission_list = None
	
	def __init__(self, pool, queue=None, ctx=None):
		self.cache = util.OrderedDict()
		self.pool = pool
		self.queue = queue
		
		self.default_grants_active = False
		self.load_permissions()
		
		if(queue and not ctx):
			raise RuntimeError("Queues can't be written to without a context.")
		
		self.ctx = ctx
		if(isinstance(ctx, (int, long))):
			self.ctx = self.get_object(ctx)
	
	def __enter__(self):
		self.begin()
		if(profile_exchange):
			self.transaction_started = time.time()
		return self
	
	def begin(self):
		self.pool.runOperation('BEGIN')
	
	def commit(self):
		if(profile_exchange):
			print '[exchange] transaction took %s seconds' % (time.time() - self.transaction_started)
		self.pool.runOperation('COMMIT')
	
	def rollback(self):
		self.pool.runOperation('ROLLBACK')
	
	def __exit__(self, etype, e, trace):
		try:
			if(etype is errors.TestError):
				self.commit()
				return False
			elif(etype is errors.UserError):
				self.commit()
				if(self.queue):
					self.queue.send(self.ctx.get_id(), dict(
						command		= 'write',
						text		= str(e),
						is_error	= True,
					))
					return True
			elif(etype is not None):
				self.rollback()
				import traceback, StringIO
				io = StringIO.StringIO()
				traceback.print_exception(etype, e, trace, None, io)
				if(self.queue):
					self.queue.send(self.ctx.get_id(), dict(
						command		= 'write',
						text		= io.getvalue(),
						is_error	= True,
					))
					return True
			else:
				self.commit()
		finally:
			self.dequeue()
	
	def get_context(self):
		return self.ctx
	
	def load_permissions(self):
		if not(ObjectExchange.permission_list):
			results = self.pool.runQuery(sql.build_select('permission'))
			ObjectExchange.permission_list = dict([(x['name'], x['id']) for x in results])
	
	def activate_default_grants(self):
		if(self.default_grants_active):
			return
		system = self.instantiate('object', default_permissions=False, id=1)
		result = self.pool.runQuery(sql.interp(
			"""SELECT v.*
				 FROM verb_name vn
				INNER JOIN verb v ON v.id = vn.verb_id
				WHERE vn.name = 'set_default_permissions'
				  AND v.origin_id = %s
			""", system.get_id()))
		
		self.instantiate('verb', default_permissions=False, *result)
		self.default_grants_active = True
	
	def instantiate(self, obj_type, record=None, *additions, **fields):
		records = []
		if(record):
			records.append(record)
		if(additions):
			records.extend(additions)
			
		default_permissions = fields.pop('default_permissions', True)
		if(fields):
			records.append(fields)
		
		results = []
		for record in records:
			object_id = record.get('id', None)
			object_key = '%s-%s' % (obj_type, object_id)
			if(object_key in self.cache):
				obj = self.cache[object_key]
			else:
				# no ID passed, we're creating a new object
				if(object_id is None):
					def fail(record):
						raise RuntimeError("Don't know how to make an object of type '%s'" % obj_type)
					
					maker = getattr(self, '_mk%s' % obj_type, fail)
					obj = maker(record)
					self.save(obj)
					
					if(default_permissions):
						try:
							self.activate_default_grants()
							system = self.get_object(1)
							set_default_permissions = system.set_default_permissions
						except (errors.NoSuchObjectError, errors.NoSuchVerbError), e:
							set_default_permissions = lambda *a: None
						finally:
							default_permissions = False
					
					set_default_permissions(obj)
				else:
					obj = self.load(obj_type, object_id)
			
			results.append(obj)
		
		if(len(records) == 1):
			return results[0]
		
		return results
	
	new = lambda self, name, *a, **kw: self.instantiate('object', *a, **dict(name=name, **kw))
	
	def _mkobject(self, record):
		obj = model.Object(self)
		
		obj._name = record.get('name', '')
		obj._unique_name = record.get('unique_name', False)
		obj._owner_id = record.get('owner_id', None)
		obj._location_id = record.get('location_id', None)
		
		return obj
	
	def _mkverb(self, record):
		origin = self.instantiate('object', id=record['origin_id'])
		v = model.Verb(origin)
		
		v._code = record.get('code', '')
		v._owner_id = record.get('owner_id', None)
		v._ability = record.get('ability', False)
		v._method = record.get('method', False)
		v._origin_id = record['origin_id']
		
		return v
	
	def _mkproperty(self, record):
		origin = self.instantiate('object', id=record['origin_id'])
		p = model.Property(origin)
		
		p._name = record['name']
		p._origin_id = record['origin_id']
		p._value = record.get('value', '')
		p._type = record.get('type', 'string')
		p._owner_id = record.get('owner_id', None)
		
		return p
	
	def _mkpermission(self, record):
		origin = None
		for origin_type in ('object', 'verb', 'property'):
			origin_id = record.get('%s_id' % origin_type, None)
			if(origin_id):
				origin = self.instantiate(origin_type, id=origin_id)
				break
		
		assert origin is not None, "Can't determine an origin for permission record: %s" % record
		
		perm = model.Permission(origin)
		
		perm.object_id = record.get('object_id', None)
		perm.verb_id = record.get('verb_id', None)
		perm.property_id = record.get('property_id', None)
		    
		perm.rule = record.get('rule', 'allow')
		perm.permission_id = record.get('permission_id', None)
		perm.type = record.get('type', 'group')
		perm.subject_id = record.get('subject_id', None)
		perm.group = record.get('group', 'everyone')
		
		return perm
	
	@defer.inlineCallbacks
	def dequeue(self):
		self.cache.clear()
		self.cache._order = []
		if(self.queue):
			try:
				yield self.queue.commit()
			except Closed, e:
				pass
	
	def load(self, obj_type, obj_id):
		obj_key = '%s-%s' % (obj_type, obj_id)
		if(obj_key in self.cache):
			return self.cache[obj_key]
		
		items = self.pool.runQuery(sql.build_select(obj_type, id=obj_id))
		if not(items):
			raise errors.NoSuchObjectError("%s #%s" % (obj_type, obj_id))
		
		def fail(record):
			raise RuntimeError("Don't know how to make an object of type '%s'" % obj_type)
		
		maker = getattr(self, '_mk%s' % obj_type, fail)
		obj = maker(items[0])
		obj.set_id(obj_id)
		self.cache[obj_key] = obj
		
		return obj
	
	def save(self, obj):
		obj_type = type(obj).__name__.lower()
		obj_id = obj.get_id()
		
		if(obj_type == 'object'):
			attribs = dict(
				name		= obj._name,
				unique_name	= ('f', 't')[obj._unique_name],
				owner_id	= obj._owner_id,
				location_id	= obj._location_id,
			)
		elif(obj_type == 'verb'):
			attribs = dict(
				code		= obj._code,
				owner_id	= obj._owner_id,
				origin_id	= obj._origin_id,
				ability		= ('f', 't')[obj._ability],
				method		= ('f', 't')[obj._method],
			)
		elif(obj_type == 'property'):
			attribs = dict(
				name		= obj._name,
				value		= obj._value,
				owner_id	= obj._owner_id,
				origin_id	= obj._origin_id,
				type		= obj._type,
			)
		else:
			raise RuntimeError("Don't know how to save an object of type '%s'" % obj_type)
		
		if(obj_id):
			self.pool.runOperation(sql.build_update(obj_type, attribs, dict(id=obj_id)))
		else:
			attribs['id'] = sql.RAW('DEFAULT')
			result = self.pool.runQuery(sql.build_insert(obj_type, attribs) + ' RETURNING id')
			obj.set_id(result[0]['id'])
		
		object_key = '%s-%s' % (obj_type, obj.get_id())
		if(object_key not in self.cache):
			self.cache[object_key] = obj
	
	def get_object(self, key, return_list=False):
		if(isinstance(key, basestring)):
			key = key.strip()
		try:
			key = int(key)
		except:
			pass
		
		if(key in ('', 'none', 'None', 'null', 'NULL')):
			return None
		
		items = None
		if(isinstance(key, basestring)):
			if(key.startswith('#')):
				end = key.find("(")
				if(end == -1):
					end = key.find( " ")
				if(end == -1):
					end = len(key)
				key = int(key[1:end])
			else:
				items = self.pool.runQuery(sql.build_select('object', name=sql.RAW(sql.interp('LOWER(%%s) = LOWER(%s)', key))))
				if(len(items) == 0):
					raise errors.NoSuchObjectError(key)
				elif(len(items) > 1):
					if(return_list):
						return self.instantiate('object', *items)
					else:
						raise errors.AmbiguousObjectError(key, items)
				else:
					return self.instantiate('object', items[0])
		
		if(isinstance(key, int)):
			if(key == -1):
				return None
			
			return self.load('object', key)
		else:
			raise ValueError("Invalid key type: %r" % repr(key))
	
	def get_parents(self, object_id, recurse=False):
		#NOTE: the heavier a parent weight is, the more influence its inheritance has.
		# e.g., if considering inheritance by left-to-right, the leftmost ancestors will
		#       have the heaviest weights.
		parent_ids = ancestor_ids = self.pool.runQuery(sql.interp(
			"""SELECT parent_id AS id
				FROM object_relation
				WHERE child_id = %s
				ORDER BY weight DESC
			""", object_id))
		while(recurse):
			ancestor_ids = self.pool.runQuery(sql.interp(
				"""SELECT parent_id AS id
					FROM object_relation
					WHERE child_id IN %s
					ORDER BY weight DESC
				""", [x['id'] for x in ancestor_ids]))
			if(ancestor_ids):
				parent_ids.extend(ancestor_ids)
			else:
				recurse = False
		
		result = self.instantiate('object', *parent_ids)
		if not(isinstance(result, (list, tuple))):
			result = [result]
		return result
	
	def has_parent(self, child_id, parent_id):
		parent_ids = [
			x['id'] for x in self.pool.runQuery(sql.interp(
				"""SELECT parent_id AS id
					FROM object_relation
					WHERE child_id = %s
					ORDER BY weight DESC
				""", child_id))
		]
		
		while(parent_ids):
			if(parent_id in parent_ids):
				return True
			parent_ids = [
				x['id'] for x in self.pool.runQuery(sql.interp(
				"""SELECT parent_id AS id
					FROM object_relation
					WHERE child_id IN %s
					ORDER BY weight DESC
				""", parent_ids))
			]
		
		return False
	
	def remove_parent(self, child_id, parent_id):
		self.pool.runOperation(sql.interp(
			"DELETE FROM object_relation WHERE child_id = %s AND parent_id = %s",
			child_id, parent_id))
	
	def add_parent(self, child_id, parent_id):
		self.pool.runOperation(sql.interp(
			"INSERT INTO object_relation (child_id, parent_id) VALUES (%s, %s)",
			child_id, parent_id))
	
	def has(self, origin_id, item_type, name, recurse=True, unrestricted=True):
		if(item_type not in ('property', 'verb')):
			raise ValueError("Invalid item type: %s" % type)
		
		a = None
		parents = [origin_id]
		while(parents):
			object_id = parents.pop(0)
			if(item_type == 'verb'):
				a = self.pool.runQuery(sql.interp(
					"""SELECT v.id
						 FROM verb v
							INNER JOIN verb_name vn ON v.id = vn.verb_id
						WHERE vn.name = %s
						  AND v.origin_id = %s
					""", name, object_id))
			elif(item_type == 'property'):
				a = self.pool.runQuery(sql.interp(
					"""SELECT p.id
						 FROM property p
						WHERE p.name = %s
						 AND p.origin_id = %s
					""", name, object_id))
			
			if(a):
				if(unrestricted):
					return True
				elif(item_type == 'verb'):
					item = self.instantiate('verb', a[0])
					return item.is_executable()
				elif(item_type == 'property'):
					item = self.instantiate('property', a[0])
					return item.is_readable()
			elif(recurse):
				results = self.pool.runQuery(sql.interp("SELECT parent_id FROM object_relation WHERE child_id = %s", object_id))
				parents.extend([result['parent_id'] for result in results])
		
		return False
	
	def get_ancestor_with(self, descendent_id, attribute_type, name):
		if(attribute_type not in ('property', 'verb')):
			raise ValueError("Invalid attribute type: %s" % type)
		
		a = None
		parents = [descendent_id]
		while(parents):
			object_id = parents.pop(0)
			if(attribute_type == 'verb'):
				a = self.pool.runQuery(sql.interp(
					"""SELECT v.origin_id AS id
						 FROM verb v
							INNER JOIN verb_name vn ON v.id = vn.verb_id
						WHERE vn.name = %s
						  AND v.origin_id = %s
					""", name, object_id))
			elif(attribute_type == 'property'):
				a = self.pool.runQuery(sql.interp(
					"""SELECT p.origin_id AS id
						 FROM property p
						WHERE p.name = %s
						 AND p.origin_id = %s
					""", name, object_id))
			
			if(a):
				break
			else:
				results = self.pool.runQuery(sql.interp("SELECT parent_id FROM object_relation WHERE child_id = %s", object_id))
				parents.extend([result['parent_id'] for result in results])
		
		if not(a):
			return None
		
		return self.instantiate('object', a[0])
	
	def get_verb(self, origin_id, name, recurse=True):
		v = None
		parents = [origin_id]
		while(parents):
			parent_id = parents.pop(0)
			v = self.pool.runQuery(sql.interp(
				"""SELECT v.*
					FROM verb v
						INNER JOIN verb_name vn ON vn.verb_id = v.id
					WHERE vn.name = %s
					  AND v.origin_id = %s
				""", name, parent_id))
			if(v or not recurse):
				break
			else:
				results = self.pool.runQuery(sql.interp("SELECT parent_id FROM object_relation WHERE child_id = %s", parent_id))
				parents.extend([result['parent_id'] for result in results])
		
		if not(v):
			return None
		
		# return self.instantiate('verb', v[0], default_permissions=(name != 'set_default_permissions'))
		verb_id = v[0]['id']
		if('verb-%s' % verb_id in self.cache):
			return self.cache['verb-%s' % verb_id]
		
		v = self._mkverb(v[0])
		v.set_id(verb_id)
		return v
	
	def remove_verb(self, origin_id, name):
		v = self.get_verb(origin_id, name)
		if(v):
			self.pool.runOperation(sql.build_delete('verb', id=v.get_id()))
	
	def get_verb_list(self, origin_id):
		verbs = self.pool.runQuery(sql.interp(
			"""SELECT v.id, array_agg(vn.name) AS names
				FROM verb v
					INNER JOIN verb_name vn ON v.id = vn.verb_id
				WHERE v.origin_id = %s
				GROUP BY v.id
			""", origin_id))
		return [dict(id=v['id'], names=','.join(v['names'])) for v in verbs]
	
	def get_property_list(self, origin_id):
		properties = self.pool.runQuery(sql.interp(
			"""SELECT p.id, p.name
				FROM property p
				WHERE p.origin_id = %s
			""", origin_id))
		return [dict(id=p['id'], name=p['name']) for p in properties]
	
	def get_verb_names(self, verb_id):
		result = self.pool.runQuery(sql.interp("SELECT name FROM verb_name WHERE verb_id = %s", verb_id))
		return [x['name'] for x in result]
	
	def add_verb_name(self, verb_id, name):
		self.pool.runOperation(sql.build_insert('verb_name', verb_id=verb_id, name=name))
	
	def remove_verb_name(self, verb_id, name):
		self.pool.runOperation(sql.build_delete('verb_name', verb_id=verb_id, name=name))
	
	def get_property(self, origin_id, name, recurse=True):
		p = None
		parents = [origin_id]
		while(parents):
			parent_id = parents.pop(0)
			p = self.pool.runQuery(sql.interp(
				"""SELECT p.*
					FROM property p
					WHERE p.name = %s
					  AND p.origin_id = %s
				""", name, parent_id))
			if(p or not recurse):
				break
			else:
				results = self.pool.runQuery(sql.interp("SELECT parent_id FROM object_relation WHERE child_id = %s", parent_id))
				parents.extend([result['parent_id'] for result in results])
		
		if not(p):
			return None
		
		# return self.instantiate('property', p[0])
		property_id = p[0]['id']
		if('property-%s' % property_id in self.cache):
			return self.cache['property-%s' % property_id]
		
		p = self._mkproperty(p[0])
		p.set_id(property_id)
		return p
	
	def remove_property(self, origin_id, name):
		v = self.get_property(origin_id, name)
		if(v):
			self.pool.runOperation(sql.build_delete('property', id=v.get_id()))
	
	def refs(self, key):
		"""
		How many objects in the store share the name given?
		"""
		result = self.pool.runQuery(sql.interp("SELECT COUNT(*) AS count FROM object WHERE name = %s", key))
		return result[0]['count']
	
	def is_unique_name(self, key):
		result = self.pool.runQuery(sql.build_select('object', dict(
			name		= sql.RAW(sql.interp('LOWER(%%s) = LOWER(%s)', key)),
			unique_name	= True
		)))
		return bool(result)
	
	def remove(self, obj_type, object_id):
		self.pool.runOperation(sql.build_delete(obj_type, id=object_id))
		self.cache.pop('%s-%s' % (obj_type, object_id), None)
	
	def is_player(self, object_id):
		result = self.pool.runQuery(sql.interp("SELECT id FROM player WHERE avatar_id = %s", object_id))
		return bool(len(result))
	
	def is_wizard(self, object_id):
		result = self.pool.runQuery(sql.interp("SELECT id FROM player WHERE wizard = 't' AND avatar_id = %s", object_id))
		return bool(len(result))
	
	def is_connected_player(self, avatar_id):
		result = self.pool.runQuery(sql.interp(
			"""SELECT 1 AS connected
				 FROM player
				WHERE COALESCE(last_login, to_timestamp(0)) > COALESCE(last_logout, to_timestamp(0))
				  AND avatar_id = %s
			""", avatar_id))
		return bool(result)
	
	def set_player(self, object_id, player=None, wizard=None, passwd=None, test_salt=None):
		if(player):
			attribs = {}
			if(passwd):
				random.shuffle(salt)
				attribs['crypt'] = crypt.crypt(passwd, test_salt or ''.join(salt[0:2]))
			if(wizard is not None):
				attribs['wizard'] = wizard
			if(self.is_player(object_id)):
				if not(attribs):
					return
				self.pool.runOperation(sql.build_update('player', attribs, dict(avatar_id=object_id)))
			else:
				if not(attribs.get('crypt')):
					raise ValueError('You must provide a password for the account.')
				attribs['wizard'] = wizard or False
				self.pool.runOperation(sql.build_insert('player', dict(avatar_id=object_id, **attribs)))
		else:
			self.pool.runOperation(sql.build_delete('player', dict(avatar_id=object_id)))

	
	def login_player(self, avatar_id):
		self.pool.runOperation(sql.build_update('player', dict(last_login=sql.RAW('now()')), dict(avatar_id=avatar_id)))
	
	def logout_player(self, avatar_id):
		self.pool.runOperation(sql.build_update('player', dict(last_logout=sql.RAW('now()')), dict(avatar_id=avatar_id)))
	
	def get_contents(self, container_id, recurse=False):
		nested_location_ids = location_ids = self.pool.runQuery(sql.interp(
			"""SELECT id
				FROM object
				WHERE location_id = %s
			""", container_id))
		while(recurse):
			location_ids = self.pool.runQuery(sql.interp(
				"""SELECT id
					FROM object
					WHERE location_id IN %s
				""", [x['id'] for x in location_ids]))
			if(location_ids):
				nested_location_ids.extend(location_ids)
			else:
				recurse = False
		return self.instantiate('object', *nested_location_ids)
	
	def find(self, container_id, name):
		match_ids = self.pool.runQuery(sql.interp(
			"""SELECT id
				FROM object
				WHERE LOWER(name) = LOWER(%s)
				  AND location_id = %s
			""", name, container_id))
		
		match_ids.extend(self.pool.runQuery(sql.interp(
			"""SELECT o.id
				FROM property p
					INNER JOIN object o ON p.origin_id = o.id
				WHERE p.name = 'name'
				  AND LOWER(p.value) = LOWER(%s)
				  AND o.location_id = %s
			""", name, container_id)))
		
		match_ids.extend(self.pool.runQuery(sql.interp(
			"""SELECT o.id
				FROM object o
					INNER JOIN object_alias oa ON oa.object_id = o.id
				WHERE LOWER(oa.alias) = LOWER(%s)
				  AND o.location_id = %s
			""", name, container_id)))
		
		return self.instantiate('object', *match_ids)
	
	def contains(self, container_id, object_id, recurse=False):
		location_ids = self.pool.runQuery(sql.interp(
			"""SELECT id
				FROM object
				WHERE location_id = %s
				ORDER BY CASE WHEN id = %s THEN 0 ELSE 1 END
			""", container_id, object_id))
		
		if(location_ids and location_ids[0]['id'] == object_id):
			return True
		
		while(recurse):
			container_ids = [x['id'] for x in location_ids]
			if(container_ids):
				location_ids = self.pool.runQuery(sql.interp(
					"""SELECT id
						FROM object
						WHERE location_id IN %s
						ORDER BY CASE WHEN id = %s THEN 0 ELSE 1 END
					""", container_ids, object_id))
			if(location_ids):
				if(location_ids[0]['id'] == object_id):
					return True
			else:
				recurse = False
		
		return False
	
	def get_access(self, object_id, type):
		return self.pool.runQuery(sql.interp(
			"""SELECT a.*, p.name AS permission_name
				FROM access a
					INNER JOIN permission p ON a.permission_id = p.id
				WHERE %s_id = %%s
				ORDER BY a.weight
			""" % type, object_id))
	
	def update_access(self, access_id, rule, access, accessor, permission, weight, subject, deleted):
		record = {} if not access_id else self.pool.runQuery(sql.interp(
			"""SELECT a.*, p.name AS permission
				FROM access a
					INNER JOIN permission p ON a.permission_id = p.id
				WHERE a.id = %s
			""", access_id))
		if(record):
			record = record[0]
		else:
			record = {}
		
		if(deleted):
			self.pool.runOperation(sql.build_delete('access', id=access_id))
			return
		
		record['rule'] = rule
		record['type'] = access
		record['weight'] = weight
		
		record.pop('group', '')
		if(access == 'group'):
			record['"group"'] = accessor
			record['accessor_id'] = None
		else:
			record['"group"'] = None
			record['accessor_id'] = accessor.get_id()
		
		if(record.pop('permission', '') != permission):
			if(permission not in self.permission_list):
				raise ValueError("Unknown permission: %s" % permission)
			record['permission_id'] = self.permission_list[permission]
		
		if(subject.get_type() == 'object'):
			record['object_id'] = subject.get_id()
		elif(subject.get_type() == 'verb'):
			record['verb_id'] = subject.get_id()
		elif(subject.get_type() == 'property'):
			record['property_id'] = subject.get_id()
		
		if(access_id):
			self.pool.runOperation(sql.build_update('access', record, dict(id=access_id)))
		else:
			self.pool.runOperation(sql.build_insert('access', **record))
	
	def is_allowed(self, accessor, permission, subject):
		if(permission not in self.permission_list):
			return False
		
		permission_id = self.permission_list[permission]
		anything_id = self.permission_list['anything']
		
		access_query = sql.build_select('access', dict(
			object_id		= subject.get_id() if isinstance(subject, model.Object) else None,
			verb_id			= subject.get_id() if isinstance(subject, model.Verb) else None,
			property_id		= subject.get_id() if isinstance(subject, model.Property) else None,
			permission_id	= (permission_id, anything_id),
			__order_by		= 'weight DESC',
		))
		
		access = self.pool.runQuery(access_query)
		
		result = False
		for rule in access:
			rule_type = (rule['rule'] == 'allow')
			if(rule['type'] == 'group'):
				if(rule['group'] not in group_definitions):
					raise ValueError("Unknown group: %s" % rule['accessor'])
				if(group_definitions[rule['group']](self, accessor, subject)):
					result = rule_type
			elif(rule['type'] == 'accessor'):
				if(rule['accessor_id'] == accessor.get_id()):
					result = rule_type
		return result
	
	def allow(self, subject, accessor, permission, create=False):
		self._grant('allow', subject, accessor, permission, create)
	
	def deny(self, subject, accessor, permission, create=False):
		self._grant('deny', subject, accessor, permission, create)
	
	def _grant(self, rule, subject, accessor, permission, create=False):
		if(isinstance(accessor, basestring) and accessor not in group_definitions):
			raise ValueError("Unknown group: %s" % accessor)
		
		if(permission in self.permission_list):
			permission_id = self.permission_list[permission]
		elif(create):
			permission_id = self.pool.runQuery(sql.build_insert('permission', dict(
				name	= permission
			)) + ' RETURNING id')[0]['id']
		else:
			raise ValueError("No such permission %r" % permission)
		
		self.pool.runOperation(sql.build_insert('access', {
			'object_id'		: subject.get_id() if isinstance(subject, model.Object) else None,
			'verb_id'		: subject.get_id() if isinstance(subject, model.Verb) else None,
			'property_id'	: subject.get_id() if isinstance(subject, model.Property) else None,
			'rule'			: rule,
			'permission_id'	: permission_id,
			'type'			: 'accessor' if isinstance(accessor, (int, long)) else 'group',
			'accessor_id'	: accessor if isinstance(accessor, (int, long)) else None,
			'"group"'		: accessor if isinstance(accessor, str) else None,
			'weight'		: 0,
		}))
	
	def validate_password(self, object_id, password):
		saved_crypt = self.pool.runQuery(sql.interp(
			"""SELECT crypt
				FROM player
				WHERE avatar_id = %s
			""", object_id))
		if not(saved_crypt):
			return False
		
		saved_crypt = saved_crypt[0]['crypt']
		
		return crypt.crypt(password, saved_crypt[0:2]) == saved_crypt
	
	def iterate_task(self, responder):
		next_task = self.pool.runQuery(
			"""SELECT t.*
				FROM task t
				WHERE t.created + (t.delay * interval '1 second') < NOW()
				  AND t.killed = 'f'
				ORDER BY t.created ASC
				LIMIT 1
			""")
		
		if not(next_task):
			return False
		
		try:
			responder.run_task(
				user_id		= next_task[0]['user_id'],
				task_id		= next_task[0]['id'],
			)
		except Exception, e:
			import traceback
			trace = traceback.format_exc()
			err = '%s: %s' % (e.__class__.__name__, str(e))
			self.pool.runOperation(sql.build_update('task', dict(killed=True, error=err, trace=trace), dict(id=next_task[0]['id'])))
			return None
		else:
			self.pool.runOperation(sql.build_delete('task', dict(id=next_task[0]['id'])))
			return True
	
	def register_task(self, user_id, delay, origin_id, verb_name, args, kwargs):
		task_id = self.pool.runQuery(sql.build_insert('task', dict(
			user_id		= user_id,
			delay		= delay,
			origin_id	= origin_id,
			verb_name	= verb_name,
			args		= args,
			kwargs		= kwargs,
		)) + ' RETURNING id')[0]['id']
		return task_id
	
	def get_task(self, task_id):
		result = self.pool.runQuery(sql.build_select('task', id=task_id))
		return result[0] if result else None
	
	def get_tasks(self, user_id=None):
		if(user_id):
			return self.pool.runQuery(sql.build_select('task', user_id=user_id))
		else:
			return self.pool.runQuery(sql.build_select('task'))
	