# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

"""
Provide access to the database
"""

import threading, random, sys, time, re, subprocess, logging

from twisted.enterprise import adbapi

from antioch import conf
from antioch.util import logs

pools = {}
async_pools = {}
pools_lock = threading.BoundedSemaphore()

RE_WS = re.compile(r'(\s+)?\t+(\s+)?')

log = logging.getLogger(__name__)

def connect(db_urls=None, *args, **kwargs):
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
	
	from antioch.core import parser

	replicated_pool = None
	for db_url in db_urls:
		dsn = parser.URL(db_url)
		
		if(dsn['scheme'] == 'postgres'):
			dsn['scheme'] = 'psycopg2'
		
		if('port' not in dsn):
			dsn['port'] = '5432'
		
		for key in dsn.keys():
			if(dsn[key] is None):
				del dsn[key]
		
		dsn['path'] = dsn['path'][1:]
		
		args += ('host=%(host)s port=%(port)s dbname=%(path)s user=%(user)s password=%(passwd)s' %  dsn
		async = kwargs.pop('async', False)
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
				log.info("reusing connection to %s" % db_url)
			else:
				if(async):
					pool = TimeoutConnectionPool(dsn['scheme'], *args, **kwargs)
				else:
					pool = SynchronousConnectionPool(dsn['scheme'], *args, **kwargs)
				selected_pools[db_url] = pool
				log.info("connecting to postgres server at %(host)s:%(port)s with %(user)s" % dsn)
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
		self.autocommit = kwargs.pop('autocommit', True)
		self.timeout = kwargs.pop('timeout', 21600)
		self.debug = kwargs.pop('debug', False)
		self.debug_writes = kwargs.pop('debug_writes', False)
		self.debug_syntax = kwargs.pop('debug_syntax', False)
		self.profile = kwargs.pop('profile', False)
		self.total_query_time = 0
		self.conn_lasttime = {}
		adbapi.ConnectionPool.__init__(self, *args, **kwargs)
	
	def connect(self, *args, **kwargs):
		"""
		Ask the ConnectionPool for a connection.
		"""
		try:
			conn = adbapi.ConnectionPool.connect(self, *args, **kwargs)
		except Exception, e:
			raise EnvironmentError("Couldn't connect to PostgreSQL server: %s" % e)
		
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
		self.debug_query(query, args, kwargs, time.time() - t)
		return result
	
	def runQuery(self, query, *args, **kwargs):
		"""
		Trivial override to provide debugging support.
		"""
		t = time.time()
		result = adbapi.ConnectionPool.runQuery(self, query, *args, **kwargs)
		self.debug_query(query, args, kwargs, time.time() - t)
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
	
	def get_total_query_time(self):
		"""
		Profiler: Return total query time since last reset.
		"""
		return self.total_query_time

	def reset_total_query_time(self):
		"""
		Profiler: Reset total query time.
		"""
		self.total_query_time = 0

	def debug_query(self, query, args, kwargs, runtime=0):
		"""
		Debug: Print the current SQL query, optionally highlighted.
		"""
		self.total_query_time += runtime
		original_query = query
		if(self.debug or self.debug_writes):
			query = '%s%s%s%s%s' % ('%s : ' % round(runtime, 6) if runtime and self.profile else '',
									re.sub(RE_WS, ' ', query),
									('', '\n')[bool(args or kwargs)],
									('', repr(args))[bool(args)],
									('', repr(kwargs))[bool(kwargs)],
								)
			
			if(self.debug_syntax):
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
					self.debug_syntax = False
					if(error):
						log.info(error.strip())
				else:
					query = output
		
		if(self.debug):
			log.info(query)
		elif(self.debug_writes and not original_query.lower().startswith('select')):
			log.info(query)



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
					log.info("Expired slave %s during operation because of %s" % (pool.connkw['host'], str(e)))
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
					log.info("Expired slave %s during query because of %s" % (pool.connkw['host'], str(e)))
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
			self.startID = None
	
	def close(self):
		"""
		Close all pool connections and shutdown the pool.
		"""
		self.finalClose()
	
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
