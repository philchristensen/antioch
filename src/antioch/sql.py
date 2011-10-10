# fu-web
#
# freelancersunion.org
#
# By Phil Christensen

"""
SQL building facilities.
"""

import types, time, datetime, array, decimal

def strftime(dt, fmt):
	"""
	Format the provided datetime object using the given format string.
	
	This function will properly format dates before 1900.
	"""
	# I hope I did this math right. Every 28 years the
	# calendar repeats, except through century leap years
	# excepting the 400 year leap years.  But only if
	# you're using the Gregorian calendar.
	
	# Created by Andrew Dalke
	# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/306860
	
	if(dt == None):
		return ''
	
	# WARNING: known bug with "%s", which is the number
	# of seconds since the epoch.	This is too harsh
	# of a check.	It should allow "%%s".
	fmt = fmt.replace("%s", "s")
	if dt.year > 1900:
		return time.strftime(fmt, dt.timetuple())
	
	year = dt.year
	# For every non-leap year century, advance by
	# 6 years to get into the 28-year repeat cycle
	delta = 2000 - year
	off = 6*(delta // 100 + delta // 400)
	year = year + off
	
	def _findall(text, substr):
		"""
		matching support function.
		"""
		# Also finds overlaps
		sites = []
		i = 0
		while 1:
			j = text.find(substr, i)
			if j == -1:
				break
			sites.append(j)
			i=j+1
		return sites
	
	# Move to around the year 2000
	year = year + ((2000 - year)//28)*28
	timetuple = dt.timetuple()
	s1 = time.strftime(fmt, (year,) + timetuple[1:])
	sites1 = _findall(s1, str(year))
	
	s2 = time.strftime(fmt, (year+28,) + timetuple[1:])
	sites2 = _findall(s2, str(year+28))
	
	sites = []
	for site in sites1:
		if site in sites2:
			sites.append(site)
	
	s = s1
	syear = "%4d" % (dt.year,)
	for site in sites:
		s = s[:site] + syear + s[site+4:]
	return s

def build_insert(table, data=None, **kwargs):
	"""
	Given a table name and a dictionary, construct an INSERT query. Keys are
	sorted alphabetically before output, so the result of passing a semantically
	identical dictionary should be the same every time.
	
	Use modu.sql.RAW to embed SQL directly in the VALUES clause.
	
	@param table: the desired table name
	@type table: str
	
	@param data: a column name to value map
	@type data: dict
	
	@returns: an SQL query
	@rtype: str
	"""
	if(data is None and kwargs):
		data = kwargs
	
	if not(data):
		raise ValueError("data argument to build_insert() is empty.")
	if not(isinstance(data, (list, tuple))):
		data = [data]
	
	keys = sorted(data[0].keys())
	
	values = []
	query = 'INSERT INTO %s (%s) VALUES ' % (table, ', '.join(keys))
	for index in range(len(data)):
		row = data[index]
		values.extend([row[key] for key in keys])
		query += '(' + ', '.join(['%s'] * len(row)) + ')'
		if(index < len(data) - 1):
			query += ', '
	
	return interp(query, *values)

def build_set(data=None, **kwargs):
	"""
	Given a dictionary, construct a SET clause. Keys are sorted alphabetically
	before output, so the result of passing a semantically identical dictionary
	should be the same every time.
	
	@param data: a column name to value map
	@type data: dict
	
	@returns: an SQL fragment
	@rtype: str
	"""
	if(data is None):
		data = {}
	data.update(kwargs)
	
	keys = data.keys()
	keys.sort()
	values = [data[key] for key in keys]
	set_clause = 'SET %s' % (', '.join(['%s = %%s'] * len(data)) % tuple(keys))
	return interp(set_clause, *values)

def build_update(table, data, constraints):
	"""
	Given a table name, a dictionary, and a set of constraints, construct an UPDATE
	query. Keys are sorted alphabetically before output, so the result of passing
	a semantically identical dictionary should be the same every time.
	
	@param table: the desired table name
	@type table: str
	
	@param data: a column name to value map
	@type data: dict
	
	@param constraints: a column name to value map
	@type constraints: dict
	
	@returns: an SQL query
	@rtype: str
	
	@seealso: L{build_where()}
	"""
	query_stub = 'UPDATE %s ' % table
	return query_stub + build_set(data) + ' ' + build_where(constraints)

def build_select(table, data=None, **kwargs):
	"""
	Given a table name and a dictionary, construct a SELECT query. Keys are
	sorted alphabetically before output, so the result of passing a semantically
	identical dictionary should be the same every time.
	
	These SELECTs always select * from a single table.
	
	Special keys can be inserted in the provided dictionary, such that:
	
		- B{__select_keyword}:	is inserted between 'SELECT' and '*'
		- B{__select_fields}:	is used after 'SELECT' instead of '*'
	
	@param table: the desired table name
	@type table: str
	
	@param data: a column name to value map
	@type data: dict
	
	@returns: an SQL query
	@rtype: str
	
	@seealso: L{build_where()}
	"""
	if(data is None):
		data = {}
	data.update(kwargs)
	
	fields = data.get('__select_fields', None)
	if(fields is None):
		fields = '*'
	else:
		if(isinstance(fields, (list, tuple))):
			fields = ','.join(fields)
		fields = '%s' % fields
	
	if('__select_keyword' in data):
		query = "SELECT %s %s FROM %s " % (data['__select_keyword'], fields, table)
	else:
		query = "SELECT %s FROM %s " % (fields, table)
	
	return query + build_where(data)

def build_delete(table, constraints=None, **kwargs):
	"""
	Given a table name, and a set of constraints, construct a DELETE query.
	Keys are sorted alphabetically before output, so the result of passing
	a semantically identical dictionary should be the same every time.
	
	@param table: the desired table name
	@type table: str
	
	@param constraints: a column name to value map
	@type constraints: dict
	
	@returns: an SQL query
	@rtype: str
	
	@seealso: L{build_where()}
	"""
	if(constraints is None):
		constraints = {}
	constraints.update(kwargs)
	query_stub = 'DELETE FROM %s ' % table
	return query_stub + build_where(constraints)

def build_where(data=None, use_where=True, **kwargs):
	"""
	Given a dictionary, construct a WHERE clause. Keys are sorted alphabetically
	before output, so the result of passing a semantically identical dictionary
	should be the same every time.
	
	Special keys can be inserted in the provided dictionary, such that:
	
		- B{__order_by}:	inserts an ORDER BY clause. ASC/DESC must be
							part of the string if you wish to use them
		- B{__limit}:		add a LIMIT clause to this query
	
	Additionally, certain types of values have alternate output:
	
		- B{list/tuple types}:		result in an IN statement
		- B{None}					results in an ISNULL statement
		- B{sql.RAW objects}:	result in directly embedded SQL, such that
									C{'col1':RAW("%s = ENCRYPT('whatever')")} equals
									C{col1 = ENCRYPT('whatever')}
		- B{persist.NOT objects}:	result in a NOT statement
	
	@param data: a column name to value map
	@type data: dict
	
	@param use_where: should the result start with "WHERE"? (Default: True)
	@type use_where: bool
	
	@returns: an SQL fragment
	@rtype: str
	"""
	if(data is None):
		data = {}
	data.update(kwargs)
	
	query = ''
	criteria = []
	values = []
	keys = data.keys()
	keys.sort()
	for key in keys:
		if(key.startswith('_')):
			continue
		value = data[key]
		if(isinstance(value, list) or isinstance(value, tuple)):
			criteria.append('%s IN (%s)' % (key, ', '.join(['%s'] * len(value))))
			values.extend(value)
		elif(isinstance(value, NOT)):
			if(isinstance(value.value, list) or isinstance(value.value, tuple)):
				criteria.append('%s NOT IN (%s)' % (key, ', '.join(['%s'] * len(value.value))))
				values.extend(value.value)
			else:
				criteria.append('%s <> %%s' % key)
				values.append(value.value)
		elif(isinstance(value, GT)):
			criteria.append('%s > %%s' % key)
			values.append(value.value)
		elif(isinstance(value, LT)):
			criteria.append('%s < %%s' % key)
			values.append(value.value)
		# This goes last, since the NOT, GT, and LT are RAW subclasses,
		# and I don't like the more specific syntax
		elif(isinstance(value, RAW)):
			if(value.value.find('%s') != -1):
				criteria.append(value.value % key)
			else:
				criteria.append('%s%s' % (key, value.value))
		elif(value is None):
			criteria.append('%s IS NULL' % key)
		else:
			criteria.append('%s = %%s' % key)
			values.append(value)
	
	if(criteria):
		if(use_where):
			query += 'WHERE '
		query += ' AND '.join(criteria)
	if('__order_by' in data):
		query += ' ORDER BY %s' % data['__order_by']
	if('__group_by' in data):
		query += ' GROUP BY %s' % data['__group_by']
	if('__limit' in data):
		query += ' LIMIT %s' % data['__limit']
	
	return interp(query, *values)

def make_list(items):
	"""
	Convert a list of things to a string suitable for use with IN.
	
	Uses interp to escape values.
	"""
	return interp(','.join(['%s'] * len(items)), *items)

def escape_sequence(seq, conv):
	return [escape_item(item, conv) for item in seq]

def escape_item(item, conv):
	return conv.get(type(item), conv[str])(item, conv)

def quoted_string_literal(s, d):
	# okay, so, according to the SQL standard, this should be all you need to do to escape
	# any kind of string.
	try:
		return "'%s'" % (s.replace("\\", "\\\\").replace("'", "''"),)
	except TypeError, e:
		raise NotImplementedError("Cannot quote %r objects: %r" % (type(s), s))

def mysql_string_literal(s, d):
	from MySQLdb import converters
	return converters.string_literal(s, d)

def interp(query, *args):
	"""
	Interpolate the provided arguments into the provided query, using
	the DB-API's default conversions, with the additional 'RAW' support
	from modu.sql.RAW2Literal
	
	@param query: A query string with placeholders
	@type query: str
	
	@param args: A list of query values
	@type args: sequence
	
	@returns: an interpolated SQL query
	@rtype: str
	"""
	
	parameters = escape_sequence(args, conversions)
	
	return query % tuple(parameters)

class RAW(object):
	"""
	Allows RAW SQL to be embedded in constructed queries.
	
	@ivar value: "Raw" (i.e., properly escaped) SQL
	"""
	def __init__(self, value):
		"""
		Create a RAW SQL fragment
		"""
		self.value = value
	
	def __repr__(self):
		"""
		Printable version.
		"""
		return "%s(%r)" % (self.__class__.__name__, self.value)


class NOT(RAW):
	"""
	Allows NOTs to be embedded in constructed queries.
	
	When sql.NOT(value) is included in the constraint array passed
	to a query building function, it will generate the SQL fragment
	'column <> value'
	
	@ivar value: The value to NOT be
	"""

class GT(RAW):
	"""
	Allow for use of a greater-than.
	
	When sql.GT(value) is included in the constraint array passed
	to a query building function, it will generate the SQL fragment
	'column > value'
	
	@ivar value: The value to be greater-than
	"""

class LT(RAW):
	"""
	Allow for use of a less-than.
	
	When sql.LT(value) is included in the constraint array passed
	to a query building function, it will generate the SQL fragment
	'column < value'
	
	@ivar value: The value to be less-than
	"""

string_literal = quoted_string_literal

conversions = {
    int: lambda s,d: str(s),
    long: lambda s,d: str(s),
    float: lambda o,d: '%.15g' % o,
    types.NoneType: lambda s,d: 'NULL',
	list: lambda s,d: '(%s)' % ','.join([escape_item(x, conversions) for x in s]),
	tuple: lambda s,d: '(%s)' % ','.join([escape_item(x, conversions) for x in s]),
    str: lambda o,d: string_literal(o, d), # default
    unicode: lambda s,d: string_literal(s.encode(), d),
    bool: lambda s,d: string_literal(('f', 't')[s], d),
    datetime.date: lambda d,c: string_literal(strftime(d, "%Y-%m-%d"), c),
    datetime.datetime: lambda d,c: string_literal(strftime(d, "%Y-%m-%d %H:%M:%S"), c),
    datetime.timedelta: lambda v,c: string_literal('%d %d:%d:%d' % (v.days, int(v.seconds / 3600) % 24, int(v.seconds / 60) % 60, int(v.seconds) % 60)),
	RAW: lambda o,d: o.value,
	decimal.Decimal: lambda s,d: str(s),
}