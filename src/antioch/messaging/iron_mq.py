# IronMQ For Python
# adapted for Twisted by Phil Christensen

from twisted.internet import defer, reactor
from twisted.web.client import HTTPClientFactory

from antioch.core import parser
from antioch.util import json

import urllib, logging
import ConfigParser

from twisted.internet import defer

log = logging.getLogger(__name__)

def file_exists(file):
	"""Check if a file exists."""
	try:
		open(file)
	except IOError:
		return False
	else:
		return True

class IllegalArgumentException(Exception):
	def __init__(self, message):
		self.message = message

	def __str__(self):
		return repr(self.message)

class IronMQ:
	DEFAULT_HOST = "mq-aws-us-east-1.iron.io"
	USER_AGENT = "IronMQ Python v0.3"

	def __init__(self, token=None, project_id=None, host=DEFAULT_HOST, port=80,
			version=1, protocol='http', config=None, app_engine=False):
		"""Prepare a configured instance of the API wrapper and return it.

		Keyword arguments:
		token -- An API token found on http://hud.iron.io. Defaults to None.
		project_id -- The ID for the project, found on http://hud.iron.io
		host -- The hostname of the API server.
				Defaults to mq-aws-us-east-1.iron.io.
		port -- The port of the API server. Defaults to 80.
		version -- The API version to use. Defaults to 1.
		protocol -- The protocol to use. Defaults to http.
		config -- The config file to draw config values from. Defaults to None.
		app_engine -- Whether to run in App Engine compatibility mode.
					  Defaults to False.
		"""
		self.token = token
		self.version = version
		self.project_id = project_id
		self.protocol = protocol
		self.host = host
		self.port = port
		self.version = version
		self.app_engine = app_engine
		if config is not None:
			config_file = ConfigParser.RawConfigParser()
			config_file.read(config)
			try:
				self.token = config_file.get("IronMQ", "token")
			except ConfigParser.NoOptionError:
				self.token = token
			try:
				self.project_id = config_file.get("IronMQ", "project_id")
			except ConfigParser.NoOptionError:
				self.project_id = project_id
			try:
				self.host = config_file.get("IronMQ", "host")
			except ConfigParser.NoOptionError:
				self.host = host
			try:
				self.port = config_file.get("IronMQ", "port")
			except ConfigParser.NoOptionError:
				self.port = port
			try:
				self.version = config_file.get("IronMQ", "version")
			except ConfigParser.NoOptionError:
				self.version = version
			try:
				self.protocol = config_file.get("IronMQ", "protocol")
			except ConfigParser.NoOptionError:
				self.protocol = protocol
		if self.token is None or self.project_id is None:
			raise IllegalArgumentException("Both token and project_id must \
					have a value")
		self.url = "%s://%s:%s/%s/" % (self.protocol, self.host, self.port,
				self.version)
		self.__setCommonHeaders()

	def __get(self, url, headers={}):
		"""Execute an HTTP GET request and return the result.

		Keyword arguments:
		url -- The url to execute the request against. (Required)
		headers -- A dict of headers to merge with self.headers and send
				   with the request.
		"""
		parsed_url = parser.URL(url)
		client = HTTPClientFactory(url,
			method		= 'GET',
			headers		= dict(headers.items() + self.headers.items()),
		)
		#client.noisy = False
		
		reactor.connectTCP(parsed_url['host'], int(parsed_url['port']), client)
		return client.deferred

	def __post(self, url, payload={}, headers={}):
		"""Execute an HTTP POST request and return the result.

		Keyword arguments:
		url -- The url to execute the request against. (Required)
		payload -- A dict of key-value form data to send with the
				   request. Will be urlencoded.
		headers -- A dict of headers to merge with self.headers and send
				   with the request.
		"""
		parsed_url = parser.URL(url)
		client = HTTPClientFactory(url,
			method		= 'POST',
			headers		= dict(headers.items() + self.headers.items()),
			postdata	= payload,
		)
		#client.noisy = False
		
		reactor.connectTCP(parsed_url['host'], int(parsed_url['port']), client)
		return client.deferred

	def __delete(self, url, payload={}, headers={}):
		"""Execute an HTTP DELETE request and return the result.

		Keyword arguments:
		url -- The url to execute the request against. (Required)
		payload -- A dict of key-value form data to send with the
				   request. Will be urlencoded.
		headers -- A dict of headers to merge with self.headers and send
				   with the request.
		"""
		parsed_url = parser.URL(url)
		client = HTTPClientFactory(url,
			method		= 'DELETE',
			headers		= dict(headers.items() + self.headers.items()),
			postdata	= payload,
		)
		#client.noisy = False
		
		reactor.connectTCP(parsed_url['host'], int(parsed_url['port']), client)
		return client.deferred

	def __setCommonHeaders(self):
		"""Modify your headers to match the JSON default values."""
		self.headers = {
			"Accept": "application/json",
			"Accept-Encoding": "gzip, deflate",
			"User-Agent": "IronMQ Python v0.3"
		}

	@defer.inlineCallbacks
	def getQueues(self, page=None, project_id=None):
		"""Execute an HTTP request to get a list of queues and return it.

		Keyword arguments:
		project_id -- The project ID to get queues from. Defaults to the
					  project ID set when initialising the wrapper.
		page -- The 0-based page to get queues from. Defaults to None, which
				omits the parameter.
		"""
		self.__setCommonHeaders()
		if project_id is None:
			project_id = self.project_id
		pageForURL = ""
		if page is not None:
			pageForURL = "&page=%s" % page
		url = "%sprojects/%s/queues?oauth=%s%s" % (self.url, project_id,
				self.token, pageForURL)
		body = yield self.__get(url)
		queues = json.loads(body)
		defer.returnValue(queues)

	@defer.inlineCallbacks
	def getQueueDetails(self, queue_name, project_id=""):
		"""Execute an HTTP request to get details on a specific queue, and
		return it.

		Keyword arguments:
		queue_name -- The name of the queue to get the details of. (Required)
		project_id -- The ID of the project the queue belongs to. Defaults to
					  the project ID set when initialising the wrapper.
		"""
		self.__setCommonHeaders()
		if project_id == "":
			project_id = self.project_id
		url = "%sprojects/%s/queues/%s?oauth=%s" % (self.url, project_id,
				queue_name, self.token)
		body = yield self.__get(url)
		queue = json.loads(body)
		defer.returnValue(queue)

	@defer.inlineCallbacks
	def deleteMessage(self, queue_name, message_id, project_id=None):
		"""Execute an HTTP request to delete a code package.

		Keyword arguments:
		queue_name -- The name of the queue the message is in. (Required)
		message_id -- The ID of the message to be deleted. (Required)
		project_id -- The ID of the project that contains the queue that
					  contains the message. Defaults to the project ID set
					  when initialising the wrapper.
		"""
		self.__setCommonHeaders()
		if project_id is None:
			project_id = self.project_id
		url = "%sprojects/%s/queues/%s/messages/%s?oauth=%s" % (self.url,
				project_id, queue_name, message_id, self.token)
		body = yield self.__delete(url)
		defer.returnValue(json.loads(body))

	@defer.inlineCallbacks
	def postMessage(self, queue_name, messages=[], project_id=None):
		"""Executes an HTTP request to create message on the queue.

		Keyword arguments:
		queue_name -- The name of the queue to add the message to. (Required)
		messages -- An array of messages to be added to the queue.
					Defaults to [].
		project_id -- The ID of the project the queue is under. Defaults to
					  the project ID set when the wrapper was initialised.
		"""
		self.__setCommonHeaders()
		if project_id is None:
			project_id = self.project_id
		url = "%sprojects/%s/queues/%s/messages?oauth=%s" % (self.url,
				project_id, queue_name, self.token)
		msgs = []
		for message in messages:
			if isinstance(message, basestring):
				msgs.append({"body": message})
			else:
				msgs.append(message)
		data = json.dumps({"messages": msgs})
		dataLen = len(data)
		headers = self.headers
		headers['Content-Type'] = "application/json"
		headers['Content-Length'] = str(dataLen)

		s = yield self.__post(url=url, payload=data, headers=headers)

		ret = json.loads(s)
		defer.returnValue(ret)

	@defer.inlineCallbacks
	def getMessage(self, queue_name, max=None, project_id=None):
		"""Executes an HTTP request to get a message off of a queue.

		Keyword arguments:
		queue_name -- The name of the queue a message is being fetched from.
					  (Required)
		max -- The maximum number of messages to pull. Defaults to 1.
		project_id -- The ID of the project that contains the queue the message
					  is to be pulled from. Defaults to the project ID set when
					  the wrapper was initialised.
		"""
		self.__setCommonHeaders()
		if project_id is None:
			project_id = self.project_id
		n = ""
		if max is not None:
			n = "&n=%s" % max
		url = "%sprojects/%s/queues/%s/messages?oauth=%s%s" % (self.url,
				project_id, queue_name, self.token, n)
		self.headers['Accept'] = "text/plain"
		try:
			del self.headers['Content-Type']
			del self.headers['Content-Length']
		except:
			pass
		body = yield self.__get(url)
		defer.returnValue(json.loads(body))
