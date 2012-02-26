# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Connect the verb environment to the database

This is the connecting thread between the database and verb code
during a transaction. it is responsible for loading and saving objects,
verbs, properties and permissions, as well as caching objects loaded
during a single verb transaction.
"""
import crypt, string, random, time, logging

from twisted.internet import defer
from twisted.python import util

from txamqp.client import Closed

from antioch.core import model, errors, messaging
from antioch.util import sql, json

group_definitions = dict(
	owners		= lambda x,a,s: a.owns(s),
	wizards		= lambda x,a,s: x.is_wizard(a.get_id()),
	everyone	= lambda x,a,s: True,
)

salt = list(string.printable[:])

rollback_after_fatal_errors = True
profile_exchange = False

log = logging.getLogger(__name__)

def extract_id(literal):
	"""
	Given an object literal, return the object ID.
	"""
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
	"""
	Database transaction layer.
	
	This class contains all the queries used to interact with the relational
	database. It doesn't take into consideration of who is calling it; that it
	dealt with by the object model itself.
	"""
	
	permission_list = None
	
	def __init__(self, pool, queue=False, ctx=None):
		"""
		Create a new object exchange.
		
		The result is attached to the provided ConnectionPool and MessageQueue, 
		and if the object context (`ctx`) is passed along, ensures rights
		enforcement for all objects.
		"""
		self.cache = util.OrderedDict()
		self.pool = pool
		self.queue = [] if queue else None
		
		self.default_grants_active = False
		self.load_permissions()
		
		if(queue and not ctx):
			raise RuntimeError("Exchanges can't use queues without a context.")
		
		self.ctx = ctx
		if(isinstance(ctx, (int, long))):
			self.ctx_id = ctx
			self.ctx = self.get_object(ctx)
		elif(ctx):
			self.ctx_id = ctx.id

	
	def __enter__(self):
		"""
		Within the cotext, wrap everything in a database transaction, and queue messages.
		"""
		self.begin()
		if(profile_exchange):
			self.transaction_started = time.time()
		return self
	
	def __exit__(self, etype, e, trace):
		"""
		Ensure that non-UserError exceptions rollback the transaction.
		"""
		try:
			show_all_traces = self.ctx and self.ctx.get('show_all_traces', False).value
		except:
			show_all_traces = False
		
		try:
			if(etype is errors.TestError):
				self.commit()
				return False
			elif(etype is EnvironmentError):
				self.rollback()
				return False
			elif(isinstance(e, errors.UserError) and not show_all_traces):
				self.commit()
				err = str(e)
				log.info('Sending normal exception to user: %s' % err)
				if(self.queue is not None):
					self.queue.append(self.ctx.get_id(), dict(
						command		= 'write',
						text		= err,
						is_error	= True,
					))
					return True
			elif(etype is not None):
				if(rollback_after_fatal_errors):
					self.rollback()
				else:
					self.commit()
				import traceback, StringIO
				io = StringIO.StringIO()
				traceback.print_exception(etype, e, trace, None, io)
				log.error('Sending fatal exception to user: %s' % str(e))
				if(self.queue is not None):
					self.queue.append(self.ctx.get_id(), dict(
						command		= 'write',
						text		= io.getvalue(),
						is_error	= True,
					))
					return True
			else:
				self.commit()
		finally:
			d = self.flush()
			d.addErrback(log.error)
	
	def begin(self):
		"""
		Start a database transaction.
		"""
		self.pool.runOperation('BEGIN')
	
	def commit(self):
		"""
		Complete a database transaction.
		"""
		if(profile_exchange):
			print '[exchange] transaction took %s seconds' % (time.time() - self.transaction_started)
		self.pool.runOperation('COMMIT')
	
	def rollback(self):
		"""
		Roll-back a database transaction.
		"""
		self.pool.runOperation('ROLLBACK')
	
	def send_message(self, user_id, msg):
		if not(self.queue):
			log.warning("attempted to send a message to user #%s on an unqueued exchange: %s" % (user_id, msg))
			return
		
		self.queue.append((user_id, msg))
	
	@defer.inlineCallbacks
	def flush(self):
		"""
		Clear and save the cache, and send all pending messages.
		"""
		self.cache.clear()
		self.cache._order = []
		if(self.queue):
			for user_id, msg in self.queue:
				queue_id = '%s-%s' % (settings.USER_QUEUE_PREFIX, user_id)
				log.debug("flushing message to #%s: %s" % (user_id, msg))
				consumer = yield messaging.get_async_consumer()
				yield consumer.send_message(queue_id, msg)
	
	def get_context(self):
		"""
		Return the user this exchange is acting in the context of.
		"""
		return self.ctx
	
	def load_permissions(self):
		"""
		Pre-load the list of existing permissions.
		"""
		if not(ObjectExchange.permission_list):
			results = self.pool.runQuery(sql.build_select('permission'))
			ObjectExchange.permission_list = dict([(x['name'], x['id']) for x in results])
	
	def activate_default_grants(self):
		"""
		Setup the default grants verb (`set_default_permissions`).
		"""
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
	
	def reload_filesystem_verbs(self):
		"""
		Clear out the code field for any verb with a filename attached.
		"""
		self.pool.runOperation("UPDATE verb SET code = '' WHERE COALESCE(filename, 'none') = filename")
	
	def instantiate(self, obj_type, record=None, *additions, **fields):
		"""
		Instantiate an object either by loading its record by ID from the database, or creating a new one.
		"""
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
					
					if(self.ctx and 'owner_id' not in record):
						record['owner_id'] = ctx.get_id()
					
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
						
						set_default_permissions(obj)
				else:
					obj = self.load(obj_type, object_id)
			
			results.append(obj)
		
		if(len(records) == 1):
			return results[0]
		
		return results
	
	def _mkobject(self, record):
		"""
		Instantiate a model.Object
		"""
		obj = model.Object(self)
		
		obj._name = record.get('name', '')
		obj._unique_name = record.get('unique_name', False)
		obj._owner_id = record.get('owner_id', None)
		obj._location_id = record.get('location_id', None)
		
		return obj
	
	def _mkverb(self, record):
		"""
		Instantiate a model.Verb
		"""
		origin = self.instantiate('object', id=record['origin_id'])
		v = model.Verb(origin)
		
		v._code = record.get('code', '')
		v._filename = record.get('filename', '')
		v._owner_id = record.get('owner_id', None)
		v._ability = record.get('ability', False)
		v._method = record.get('method', False)
		v._origin_id = record['origin_id']
		
		if('name' in record):
			self.save(v)
			v.add_name(record['name'])
		
		return v
	
	def _mkproperty(self, record):
		"""
		Instantiate a model.Property
		"""
		origin = self.instantiate('object', id=record['origin_id'])
		p = model.Property(origin)
		
		p._name = record['name']
		p._origin_id = record['origin_id']
		p._type = record.get('type', 'string')
		p._owner_id = record.get('owner_id', None)
		
		val = record.get('value', '')
		p._value = json.loads(val, exchange=self) if val else val
		
		return p
	
	def _mkpermission(self, record):
		"""
		Instantiate a model.Permission
		"""
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
	
	def load(self, obj_type, obj_id):
		"""
		Load a specific object from the database.
		"""
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
		if not(obj.get_id()):
			obj.set_id(obj_id)
		self.cache[obj_key] = obj
		
		return obj
	
	def save(self, obj):
		"""
		Save the provided model back into the database.
		"""
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
				filename	= obj._filename,
				owner_id	= obj._owner_id,
				origin_id	= obj._origin_id,
				ability		= ('f', 't')[obj._ability],
				method		= ('f', 't')[obj._method],
			)
		elif(obj_type == 'property'):
			def check(v):
				if(v is None):
					return False
				elif(v is ""):
					return False
				return True
			
			attribs = dict(
				name		= obj._name,
				value		= json.dumps(obj._value) if check(obj._value) else obj._value,
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
		"""
		Return the object specified by the provided key.
		
		If return_list is True, ambiguous object keys will return a list
		of matching objects.
		"""
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
					if(return_list):
						return []
					else:
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
	
	def get_aliases(self, object_id):
		"""
		Return all aliases for the given object ID.
		"""
		result = self.pool.runQuery(sql.interp("SELECT alias FROM object_alias WHERE object_id = %s", object_id))
		return [x['alias'] for x in result] 
	
	def add_alias(self, object_id, alias):
		"""
		Add an aliases for the provided object.
		"""
		self.pool.runOperation(sql.build_insert('object_alias', object_id=object_id, alias=alias));
	
	def remove_alias(self, object_id, alias):
		"""
		Remove an aliases for the provided object.
		"""
		self.pool.runOperation(sql.build_delete('object_alias', object_id=object_id, alias=alias));
	
	def get_observers(self, object_id):
		"""
		Get a list of objects currently observing the provided object.
		"""
		result = self.instantiate('object', *self.pool.runQuery(sql.interp(
			"""SELECT o.*
				FROM object o
				INNER JOIN object_observer oo ON oo.observer_id = o.id
				WHERE oo.object_id = %s
			""", object_id)))
		if not(isinstance(result, (list, tuple))):
			result = [result]
		return result
	
	def get_observing(self, object_id):
		"""
		Get the object that the provided object is observing.
		"""
		result = self.instantiate('object', *self.pool.runQuery(sql.interp(
			"""SELECT o.*
				FROM object o
				INNER JOIN object_observer oo ON oo.object_id = o.id
				WHERE oo.observer_id = %s
			""", object_id)))
		if(isinstance(result, (list, tuple))):
			return result[0] if result else None
		return result
	
	def clear_observers(self, object_id):
		"""
		Make all current observers stop paying attention to the provided object.
		"""
		self.pool.runOperation(sql.build_delete('object_observer', object_id=object_id));
	
	def add_observer(self, object_id, observer_id):
		"""
		Add an observer for the provided object.
		"""
		self.pool.runOperation(sql.build_insert('object_observer', object_id=object_id, observer_id=observer_id));
	
	def remove_observer(self, object_id, observer_id):
		"""
		Remove an observer for the provided object.
		"""
		self.pool.runOperation(sql.build_delete('object_observer', object_id=object_id, observer_id=observer_id));
	
	def get_parents(self, object_id, recurse=False):
		"""
		Return a list of immediate parents for the given object.
		
		Optionally, pass recurse=True to fetch complete ancestry.
		"""
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
		return [result] if isinstance(result, model.Object) else result
	
	def has_parent(self, child_id, object_id):
		"""
		Does this child have the provided object as an ancestor?
		"""
		parent_ids = [
			x['id'] for x in self.pool.runQuery(sql.interp(
				"""SELECT parent_id AS id
					FROM object_relation
					WHERE child_id = %s
					ORDER BY weight DESC
				""", child_id))
		]
		
		while(parent_ids):
			if(object_id in parent_ids):
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
		"""
		Remove the given parent from this child's list of immediate ancestors.
		"""
		self.pool.runOperation(sql.interp(
			"DELETE FROM object_relation WHERE child_id = %s AND parent_id = %s",
			child_id, parent_id))
	
	def add_parent(self, child_id, parent_id):
		"""
		Add the given parent to this child's list of immediate ancestors.
		"""
		self.pool.runOperation(sql.interp(
			"INSERT INTO object_relation (child_id, parent_id) VALUES (%s, %s)",
			child_id, parent_id))
	
	def has(self, origin_id, item_type, name, recurse=True, unrestricted=True):
		"""
		Does the given origin item have a certain verb or property in its ancestry?
		"""
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
		"""
		Return the ancestor object that provides the given attribute.
		"""
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
		"""
		Get a verb by this name, recursing by default.
		"""
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
		v._source_id = origin_id
		return v
	
	def remove_verb(self, origin_id, name):
		"""
		Remove a verb defined directly on the given object.
		"""
		v = self.get_verb(origin_id, name)
		if(v):
			self.pool.runOperation(sql.build_delete('verb', id=v.get_id()))
	
	def get_verb_list(self, origin_id):
		"""
		Get a list of verb id and names dictionaries.
		"""
		verbs = self.pool.runQuery(sql.interp(
			"""SELECT v.id, array_agg(vn.name) AS names
				FROM verb v
					INNER JOIN verb_name vn ON v.id = vn.verb_id
				WHERE v.origin_id = %s
				GROUP BY v.id
			""", origin_id))
		return [dict(id=v['id'], names=','.join(v['names'])) for v in verbs]
	
	def get_property_list(self, origin_id):
		"""
		Get a list of property id and name dictionaries.
		"""
		properties = self.pool.runQuery(sql.interp(
			"""SELECT p.id, p.name
				FROM property p
				WHERE p.origin_id = %s
			""", origin_id))
		return [dict(id=p['id'], name=p['name']) for p in properties]
	
	def get_verb_names(self, verb_id):
		"""
		Get a list of names for the given verb.
		"""
		result = self.pool.runQuery(sql.interp("SELECT name FROM verb_name WHERE verb_id = %s", verb_id))
		return [x['name'] for x in result]
	
	def add_verb_name(self, verb_id, name):
		"""
		Add another name for a given verb.
		"""
		self.pool.runOperation(sql.build_insert('verb_name', verb_id=verb_id, name=name))
	
	def remove_verb_name(self, verb_id, name):
		"""
		Remove a name for a given verb.
		"""
		self.pool.runOperation(sql.build_delete('verb_name', verb_id=verb_id, name=name))
	
	def get_property(self, origin_id, name, recurse=True):
		"""
		Get a property defined on an ancestor of the given origin_id.
		"""
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
		p._source_id = origin_id
		return p
	
	def remove_property(self, origin_id, name):
		"""
		Remove a property defined on the given object
		"""
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
		"""
		Has the given key been designated as a unique name?
		"""
		result = self.pool.runQuery(sql.build_select('object', dict(
			name		= sql.RAW(sql.interp('LOWER(%%s) = LOWER(%s)', key)),
			unique_name	= True
		)))
		return bool(result)
	
	def remove(self, obj_type, object_id):
		"""
		Destroy an object in the database.
		"""
		self.pool.runOperation(sql.build_delete(obj_type, id=object_id))
		self.cache.pop('%s-%s' % (obj_type, object_id), None)
	
	def is_player(self, object_id):
		"""
		Is the given object the avatar for a player?
		"""
		result = self.pool.runQuery(sql.interp("SELECT id FROM player WHERE avatar_id = %s", object_id))
		return bool(len(result))
	
	def is_wizard(self, avatar_id):
		"""
		Does the given player have wizard rights?
		"""
		result = self.pool.runQuery(sql.interp("SELECT id FROM player WHERE wizard = 't' AND avatar_id = %s", avatar_id))
		return bool(len(result))
	
	def is_connected_player(self, avatar_id):
		"""
		Is the given player currently logged on?
		"""
		result = self.pool.runQuery(sql.interp(
			"""SELECT 1 AS connected
				 FROM player
				WHERE COALESCE(last_login, to_timestamp(0)) > COALESCE(last_logout, to_timestamp(0))
				  AND avatar_id = %s
			""", avatar_id))
		return bool(result)
	
	def set_player(self, object_id, player=None, wizard=None, passwd=None, test_salt=None):
		"""
		Edit the player attributes of an object.
		"""
		if(player is not False):
			attribs = {}
			if(passwd):
				random.shuffle(salt)
				attribs['crypt'] = crypt.crypt(passwd, test_salt or ''.join(salt[0:2]))
			else:
				attribs['crypt'] = '!'
			if(wizard is not None):
				attribs['wizard'] = wizard
			if(self.is_player(object_id)):
				if not(attribs):
					return
				self.pool.runOperation(sql.build_update('player', attribs, dict(avatar_id=object_id)))
			else:
				attribs['wizard'] = wizard or False
				self.pool.runOperation(sql.build_insert('player', dict(avatar_id=object_id, **attribs)))
		else:
			self.pool.runOperation(sql.build_delete('player', dict(avatar_id=object_id)))

	
	def login_player(self, avatar_id, session_id):
		"""
		Register a player as logged in.
		"""
		self.pool.runOperation(sql.build_update('player', dict(session_id=session_id, last_login=sql.RAW('now()')), dict(avatar_id=avatar_id)))
	
	def logout_player(self, avatar_id):
		"""
		Register a player as logged out.
		"""
		self.pool.runOperation(sql.build_update('player', dict(last_logout=sql.RAW('now()')), dict(avatar_id=avatar_id)))
	
	def get_last_client_ip(self, avatar_id):
		"""
		Get the last IP used to login as this player.
		"""
		result = self.pool.runQuery(sql.build_select('session', user_id=avatar_id))
		return result[0]['last_client_ip'] if result else None
	
	def get_contents(self, container_id, recurse=False):
		"""
		Get the immediate contents of a provided object.
		
		Optionally supply recurse=True to fetch all contents.
		"""
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
		result = self.instantiate('object', *nested_location_ids)
		return [result] if isinstance(result, model.Object) else result
	
	def find(self, container_id, name):
		"""
		Find an object immediately inside the provided container.
		"""
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
			""", '"%s"' % name, container_id)))
		
		match_ids.extend(self.pool.runQuery(sql.interp(
			"""SELECT o.id
				FROM object o
					INNER JOIN object_alias oa ON oa.object_id = o.id
				WHERE LOWER(oa.alias) = LOWER(%s)
				  AND o.location_id = %s
			""", name, container_id)))
		
		return self.instantiate('object', *match_ids)
	
	def contains(self, container_id, object_id, recurse=False):
		"""
		Is the provided object immediately contained by the provided container object?
		
		Optionally supply recurse=True to check for any containment.
		"""
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
		"""
		Return the access list for a particular entity.
		"""
		return self.pool.runQuery(sql.interp(
			"""SELECT a.*, p.name AS permission_name
				FROM access a
					INNER JOIN permission p ON a.permission_id = p.id
				WHERE %s_id = %%s
				ORDER BY a.weight
			""" % type, object_id))
	
	def update_access(self, access_id, rule, access, accessor, permission, weight, subject, deleted):
		"""
		Modify an access rule.
		"""
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
		"""
		Is `accessor` allowed to do `permission` on `subject`?.
		"""
		if(permission not in self.permission_list):
			import warnings
			warnings.warn("Unknown permission encountered: %s" % permission)
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
		"""
		Add an allow rule.
		"""
		self._grant('allow', subject, accessor, permission, create)
	
	def deny(self, subject, accessor, permission, create=False):
		"""
		Add a deny rule.
		"""
		self._grant('deny', subject, accessor, permission, create)
	
	def _grant(self, rule, subject, accessor, permission, create=False):
		"""
		Add an access rule.
		"""
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
	
	def validate_password(self, avatar_id, password):
		"""
		Match the given password for the provided avatar.
		"""
		saved_crypt = self.pool.runQuery(sql.interp(
			"""SELECT crypt
				FROM player
				WHERE avatar_id = %s
			""", avatar_id))
		if not(saved_crypt):
			return False
		
		saved_crypt = saved_crypt[0]['crypt']
		
		return crypt.crypt(password, saved_crypt[0:2]) == saved_crypt
	
	def iterate_task(self, responder):
		"""
		Check for waiting tasks using the given ampoule TransactionChild.
		
		Returns False if there's no task waiting
		Returns None if an exception occurs
		Returns True if it processes a task
		"""
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
		"""
		Register a delayed verb call.
		"""
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
		"""
		Fetch the record for the provided task id.
		"""
		result = self.pool.runQuery(sql.build_select('task', id=task_id))
		return result[0] if result else None
	
	def get_tasks(self, user_id=None):
		"""
		Get a list of waiting tasks.
		"""
		if(user_id):
			return self.pool.runQuery(sql.build_select('task', user_id=user_id))
		else:
			return self.pool.runQuery(sql.build_select('task'))
	