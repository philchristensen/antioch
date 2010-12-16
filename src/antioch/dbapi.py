# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Provide access to the database
"""

import threading, random, sys, time, re, subprocess

from twisted.enterprise import adbapi

debug = False
profile_debug = False
debug_stream = sys.stderr
debug_syntax_highlighting = False

pools = {}
async_pools = {}
pools_lock = threading.BoundedSemaphore()

URL_REGEXP = r'(?P<dbapiName>[+a-z0-9]+)\:(\/\/)?'
URL_REGEXP += r'((?P<user>\w+?)(\:(?P<passwd>\w+?))?\@)?'
URL_REGEXP += r'(?P<host>[\._\-a-z0-9]+)(\:(?P<port>\d+))?'
URL_REGEXP += r'(?P<db>/[^\s;?#]*)(;(?P<params>[^\s?#]*))?'
URL_REGEXP += r'(\?(?P<query>[^\s#]*))?(\#(?P<fragment>[^\s]*))?'
URL_RE = re.compile(URL_REGEXP, re.IGNORECASE)

RE_WS = re.compile(r'(\s+)?\t+(\s+)?')

total_query_time = 0

def get_total_query_time():
	"""
	Profiler: Return total query time since last reset.
	"""
	return total_query_time

def reset_total_query_time():
	"""
	Profiler: Reset total query time.
	"""
	global total_query_time
	total_query_time = 0

def sql_debug(query, args, kwargs, runtime=0):
	"""
	Debug: Print the current SQL query, optionally highlighted.
	"""
	global total_query_time
	total_query_time += runtime
	original_query = query
	if(debug):
		query = '%s%s%s%s%s' % ('%s : ' % round(runtime, 6) if runtime and profile_debug else '',
								re.sub(RE_WS, ' ', query),
								('', '\n')[bool(args or kwargs)],
								('', repr(args))[bool(args)],
								('', repr(kwargs))[bool(kwargs)],
							)
		
		global debug_syntax_highlighting
		if(debug_syntax_highlighting):
			command = 'source-highlight -s sql -f esc'
			sub = subprocess.Popen(command,
				stdin	= subprocess.PIPE,
				stdout	= subprocess.PIPE,
				stderr	= subprocess.PIPE,
				shell	= True,
				universal_newlines = True
			)
			
			error = ''
			try:
				output, error = sub.communicate(input=query)
				if(sub.returncode):
					raise RuntimeError("syntax highlighter subprocess returned %s" % sub.returncode)
			except:
				debug_syntax_highlighting = False
				if(error):
					print >>debug_stream, error.strip()
			else:
				query = output
	
	if(debug is True):
		print >>debug_stream, query
	elif(debug and not original_query.lower().startswith('select')):
		print >>debug_stream, query

def connect(db_urls=None, async=False, *args, **kwargs):
	"""
	Get a new connection pool for a particular db_url.
	
	Accepts a DSN specified as a URL, and returns a new
	connection pool object. If `async` is False (the default),
	all database requests are made synchronously.
	
	@param db_url: A URL of the form C{drivername://user:password@host/dbname}
	@type db_url: str
	
	@param async: if True, create an asynchronous connection pool object.
	@type async: bool
	
	@param *args: other positional arguments to pass to the DB-API driver.
	@param **kwargs: other keyword arguments to pass to the DB-API driver.
	"""
	if(isinstance(db_urls, list)):
		raise ValueError('Replicated databases must be provided as a tuple, not a list')
	if not(isinstance(db_urls, tuple)):
		db_urls = (db_urls,)
	
	replicated_pool = None
	for db_url in db_urls:
		match = URL_RE.match(db_url)
		dsn = match.groupdict()
		
		for key in dsn.keys():
			if(dsn[key] is None):
				del dsn[key]
		
		args += ('host=%s dbname=%s user=%s password=%s' % (dsn['host'], dsn['db'][1:], dsn['user'], dsn['passwd']),)
		
		kwargs.update(dict(
			cp_reconnect	= True,
			cp_noisy		= False,
			cp_min			= 10,
			cp_max			= 15,
		))
		
		global pools, async_pools, pools_lock
		pools_lock.acquire()
		try:
			if(async):
				selected_pools = async_pools
			else:
				selected_pools = pools
			
			if(db_url in selected_pools):
				pool = selected_pools[db_url]
			else:
				if(async):
					pool = TimeoutConnectionPool(dsn['dbapiName'], *args, **kwargs)
				else:
					pool = SynchronousConnectionPool(dsn['dbapiName'], *args, **kwargs)
				selected_pools[db_url] = pool
		finally:
			pools_lock.release()
		
		if(len(db_urls) == 1):
			return pool
		elif(replicated_pool):
			replicated_pool.add_slave(pool)
		else:
			replicated_pool = ReplicatedConnectionPool(pool)
	
	return replicated_pool

class TimeoutConnectionPool(adbapi.ConnectionPool):
	"""
	This ConnectionPool will automatically expire connections according to a timeout value.
	"""
	def __init__(self, *args, **kwargs):
		self.timeout = kwargs.pop('timeout', 21600)
		self.conn_lasttime = {}
		self.autocommit = kwargs.pop('autocommit', True)
		adbapi.ConnectionPool.__init__(self, *args, **kwargs)
	
	def connect(self, *args, **kwargs):
		"""
		Ask the ConnectionPool for a connection.
		"""
		conn = adbapi.ConnectionPool.connect(self, *args, **kwargs)
		
		if(self.timeout > 3600):
			tid = self.threadID()
			lasttime = self.conn_lasttime.get(tid, 0)
			now = time.time()
			if not(lasttime):
				self.conn_lasttime[tid] = lasttime = now
			
			if(now - lasttime >= self.timeout):
				self.disconnect(conn)
				conn = adbapi.ConnectionPool.connect(self, *args, **kwargs)
			
			self.conn_lasttime[tid] = now
		
		return conn
	
	def runOperation(self, query, *args, **kwargs):
		"""
		Trivial override to provide debugging support.
		"""
		t = time.time()
		result = adbapi.ConnectionPool.runOperation(self, query, *args, **kwargs)
		sql_debug(query, args, kwargs, time.time() - t)
		return result
	
	def runQuery(self, query, *args, **kwargs):
		"""
		Trivial override to provide debugging support.
		"""
		t = time.time()
		result = adbapi.ConnectionPool.runQuery(self, query, *args, **kwargs)
		sql_debug(query, args, kwargs, time.time() - t)
		return result
	
	def _runInteraction(self, interaction, *args, **kw):
		"""
		An internal function to run a SQL statement through one of the connections in this pool.
		
		This version of the method ensures that all drivers return a column->value dict. This
		can also be handled by the driver layer itself (e.g., by selecting a particular
		cursor type).
		"""
		conn = adbapi.Connection(self)
		trans = adbapi.Transaction(self, conn)
		try:
			result = interaction(trans, *args, **kw)
			if(result and isinstance(result, (list, tuple)) and isinstance(result[0], (list, tuple))):
				result = [dict(zip([c[0] for c in trans._cursor.description], item)) for item in result]
			trans.close()
			if(self.autocommit):
				conn.commit()
			return result
		except:
			if(self.autocommit):
				conn.rollback()
			raise


class ReplicatedConnectionPool(object):
	"""
	A collection of database servers in a replicated environment.
	
	Queries are examined to see if there are SELECTs, with all
	reads being sent to the slaves in round-robin mode, and all
	writes are sent to the master.
	
	When write_only_master is True, the master server is not
	used for reads. Otherwise it is included in the round-robin
	of servers to read from.
	
	If there are no slaves, all queries are sent to the master.
	"""
	def __init__(self, master, write_only_master=False):
		"""
		Set up a replicated DB connection.
		
		Given an initial master server, initialize a deque to be
		used to store slaves and select them via round-robin.
		"""
		self.master = master
		self.slaves = []
		if not(write_only_master):
			self.slaves.append(self.master)
		self.selected_slave = None
	
	def add_slave(self, pool):
		"""
		Add a ConnectionPool as a slave.
		"""
		if(pool not in self.slaves):
			self.slaves.append(pool)
	
	def runOperation(self, query, *args, **kwargs):
		"""
		Run an operation on the master.
		
		Note that even though 'operations' (e.g., inserts, deletes, updates)
		should always be on the master, we still check the query, since
		it could just be a programming error.
		"""
		pool = self.getPoolFor(query)
		while(pool):
			try:
				pool.runOperation(query, *args, **kwargs)
				break
			except adbapi.ConnectionLost, e:
				if(pool == self.master):
					raise e
				else:
					print >>sys.stderr, "Expired slave %s during operation because of %s" % (pool.connkw['host'], str(e))
					try:
						self.slaves.remove(pool)
						pool.close()
					except:
						pass
					pool = self.getPoolFor(query)
	
	def runQuery(self, query, *args, **kwargs):
		"""
		Run a query on a slave.
		
		Note that even though 'queries' (e.g., selects) should always be on 
		a slave, we still check the query, since it could just be a programming error.
		"""
		pool = self.getPoolFor(query)
		while(pool):
			try:
				return pool.runQuery(query, *args, **kwargs)
			except adbapi.ConnectionLost, e:
				if(pool == self.master):
					raise e
				else:
					print >>sys.stderr, "Expired slave %s during query because of %s" % (pool.connkw['host'], str(e))
					try:
						self.slaves.remove(pool)
						pool.close()
					except:
						pass
					pool = self.getPoolFor(query)
	
	def runInteraction(self, interaction, *args, **kwargs):
		"""
		Run an interaction on the master.
		"""
		return self.master.runInteraction(interaction, *args, **kwargs)
	
	def runWithConnection(self, func, *args, **kwargs):
		"""
		Run a function, providing the connection object for the master.
		"""
		return self.master.runWithConnection(func, *args, **kwargs)
	
	def getSlave(self):
		"""
		Return the next slave in the round robin.
		"""
		if not(self.slaves):
			return self.master
		# if selected slave is None, it won't be in slaves either
		if(self.selected_slave not in self.slaves):
			random.shuffle(self.slaves)
			self.selected_slave = self.slaves[-1]
			#print >>sys.stderr, "Selected slave is now: %s" % self.selected_slave.connkw['host']
		return self.selected_slave
	
	def getPoolFor(self, query):
		"""
		Return a slave if this is a SELECT query, else return the master.
		"""
		test_string = query.lower()
		if(test_string.startswith('select')):
			result = self.getSlave()
		elif(test_string.startswith('create temporary table')):
			result = self.getSlave()
		elif(test_string.startswith('drop temporary table')):
			result = self.getSlave()
		else:
			# if(self.selected_slave and self.master != self.selected_slave):
			# 	print >>sys.stderr, "Selected slave is now: %s" % self.selected_slave.connkw['host']
			result = self.selected_slave = self.master
		
		return result

class SynchronousConnectionPool(TimeoutConnectionPool):
	"""
	This trvial subclass disables thread creation within the ConnectionPool
	object so that it may be used from within a syncronous application
	"""
	def __init__(self, dbapiName, *connargs, **connkw):
		"""
		Create a new instance of the connection pool.
		
		This overridden constructor makes sure the Twisted reactor
		doesn't get started in non-twisted.web-hosted environments.
		"""
		TimeoutConnectionPool.__init__(self, dbapiName, *connargs, **connkw)
		from twisted.internet import reactor
		if(self.startID):
			reactor.removeSystemEventTrigger(self.startID)
	
	def _runOperation(self, trans, *args, **kw):
		"""
		Return the results of an operation.
		"""
		return trans.execute(*args, **kw)
	
	def runInteraction(self, interaction, *args, **kw):
		"""
		Run a function, passing it a cursor from this pool.
		
		This version of the method does not spawn a thread, and so returns
		the result directly, instead of a Deferred.
		"""
		return self._runInteraction(interaction, *args, **kw)
	
	def runWithConnection(self, func, *args, **kw):
		"""
		Run a function, passing it one of the connections in this pool.
		
		This version of the method does not spawn a thread, and so returns
		the result directly, instead of a Deferred.
		"""
		return self._runWithConnection(func, *args, **kw)
