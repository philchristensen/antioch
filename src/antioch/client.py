# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Implement the web interface
"""

import os, os.path, time

import pkg_resources as pkg

from zope.interface import implements

from twisted.application import service, internet
from twisted.internet import reactor, defer, task
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.cred import credentials
from twisted.python import failure, log

from nevow import inevow, loaders, athena, guard, rend, tags

from txamqp import content
from txamqp.queue import Closed

from antioch import errors, assets, transact, session, modules, json

class Mind(object):
	"""
	Represents a client connection.
	"""
	def __init__(self, request, credentials):
		"""
		Hold on to IP address info for the client.
		
		@param request: the current web request
		@type request: L{twisted.web.http.Request}
		
		@param credentials: the supplied user credentials
		"""
		self.addr = request.transport.client
		self.remote_host = self.addr[0]


class RootDelegatePage(rend.Page):
	login_url = '/login'
	logout_url = '/logout'
	client_url = '/universe'
	
	def __init__(self, spool, msg_service, portal):
		"""
		Create a new root delegate page connected to the given session pool and portal.
		
		@param spool: the current session store
		@type spool: L{antioch.session.IUserSessionStore}
		
		@param portal: the current auth portal
		@param portal: L{twisted.cred.portal.Portal}
		"""
		self.spool = spool
		self.portal = portal
		self.msg_service = msg_service
		self.connections = {}
		
		#assets.enable_assets(self, assets)
		assets.enable_assets(self)
	
	@inlineCallbacks
	def locateChild(self, ctx, segments):
		"""
		Take care of authentication while returning Resources or redirecting.
		
		@param ctx: request context
		
		@param segments: list of remaining path segments
		@type segments: tuple
		
		@return: child resource
		"""
		user, sid = yield self.authenticate(ctx)
		
		# some path specified
		if(segments):
			# session is logged in
			if(user):
				if(segments[0] == 'universe'):
					mind = Mind(inevow.IRequest(ctx), None)
					if(len(segments) > 1):
						client = self.connections[sid]
					else:
						client = self.connections[sid] = ClientInterface(user, mind, self.msg_service, sid)
					returnValue((client, segments[1:]))
				elif(len(segments) > 1 and segments[0] == 'plugin'):
					mod = modules.get(segments[1])
					if(mod):
						returnValue((mod.get_resource(user), segments[2:]))
				elif(segments[0] == 'logout'):
					self.spool.logoutUser(sid)
					if(sid in self.connections):
						del self.connections[sid]
					request = inevow.IRequest(ctx)
					request.redirect('/login')
					returnValue((ClientLogin(self.spool, self.portal), segments[1:]))
			# not logged in, at login page
			elif(segments[0] == 'login'):
				returnValue((ClientLogin(self.spool, self.portal), segments[1:]))
			# usually because server restarted or was bookmarked
			# redirect to the login page for convenience
			elif(segments[0] in ('logout', 'universe')):
				request = inevow.IRequest(ctx)
				request.redirect('/login')
				returnValue((ClientLogin(self.spool, self.portal), segments[1:]))
		
		# let renderHTTP take care of the redirect to /login or /universe
		returnValue(super(RootDelegatePage, self).locateChild(ctx, segments))
	
	@inlineCallbacks
	def renderHTTP(self, ctx):
		"""
		Redirect either to the client interface or a login form.

		@param ctx: request context
		
		@return: empty string unless we're going to redirect, which we always do
		"""
		result = yield self.authRedirect(ctx)
		if not(result):
			request = inevow.IRequest(ctx)
			request.redirect('/universe')
		returnValue('')
	
	@inlineCallbacks
	def authenticate(self, ctx):
		"""
		Authenticate the current session.
		
		@param ctx: request context
		
		@return: the user object and session ID
		@rtype: tuple(dict, str)
		"""
		request = inevow.IRequest(ctx)

		creds = session.getSessionCredentials(ctx)
		iface, user, logout = yield self.portal.login(creds, None, inevow.IResource)
		yield session.updateSession(self.spool, request, user)
		
		if(session.ISessionCredentials.providedBy(creds)):
			sid = creds.getSid()
		else:
			sid = None
		
		returnValue((user, sid))
	
	@inlineCallbacks
	def authRedirect(self, ctx):
		"""
		Authenticate the current session, redirecting to login if necessary.
		
		@param ctx: request context
		
		@return: False if the user is already authenticated, redirects if not.
		@rtype: bool
		"""
		user, sid = yield self.authenticate(ctx)
		if(user is None):
			request = inevow.IRequest(ctx)
			request.redirect('/login')
			returnValue(True)
		returnValue(False)
	

class ClientLogin(rend.Page):
	"""
	The primary login form.
	
	This page is extremely simple and could easily be replaced by another
	page that simple posts to this location instead.
	"""
	implements(inevow.IResource)
	
	def __init__(self, spool, portal):
		"""
		Provide the necessary objects to handle session saving.
		
		@param spool: connection to the session database pool
		@type spool: L{session.TransactionUserSessionStore}
		"""
		super(ClientLogin, self).__init__()
		self.docFactory = loaders.xmlstr(pkg.resource_string('antioch.assets', 'templates/client-login.xml'))
		self.portal = portal
		self.spool = spool
	
	@inlineCallbacks	
	def renderHTTP(self, ctx):
		"""
		Present the login form and handle login on POST.
		
		@param ctx: request context
		"""
		request = inevow.IRequest(ctx)
		if(request.fields is not None):
			username = ''
			password = ''
			if('username' in request.fields):
				username = request.fields['username'].value
			if('password' in request.fields):
				password = request.fields['password'].value
			
			creds = credentials.UsernamePassword(username, password)
			
			iface, user, logout = yield self.portal.login(creds, None, inevow.IResource)
			yield session.updateSession(self.spool, request, user)
			
			if(user):
				request.redirect('/universe')
				returnValue('')
			
		result = yield super(ClientLogin, self).renderHTTP(ctx)
		returnValue(result)
	

class ClientInterface(athena.LivePage):
	"""
	The primary client interface.
	
	This page maintains an Athena connection to the server by using
	the LiveElement `ClientConnector`. If this page is closed, any
	child windows will stop working, as they use the parent's
	connection to the server, instead of having their own.
	"""
	#TRANSPORTLESS_DISCONNECT_TIMEOUT = 300
	#TRANSPORT_IDLE_TIMEOUT = 30
	
	def __init__(self, user, mind, msg_service, session_id):
		"""
		Setup the client interface.
		
		@param user: user record from player table
		@type user: dict
		
		@param mind: opaque object with ip_address and other info
		@type mind: C{Mind}
		
		@param msg_service: reference to the current process' message service
		@type msg_server: L{message.MessageService}
		"""
		super(ClientInterface, self).__init__()
		
		self.msg_service = msg_service
		
		self.user_id = user['avatar_id']
		self.session_id = session_id
		self.mind = mind
		self.docFactory = loaders.xmlstr(pkg.resource_string('antioch.assets', 'templates/client.xml'))
		self.connector = None
		self.notifyOnDisconnect().errback = self.logout
	
	def logout(self, *args, **kwargs):
		"""
		Window closed, logout from the connection.
		"""
		if(self.connector):
			self.connector.logout(*args, **kwargs)
		else:
			raise RuntimeError("Logout called before LiveElement was rendered.")
	
	@defer.inlineCallbacks
	def render_ClientConnector(self, ctx, data):
		"""
		Render the Athena connection element.
		
		@param ctx: request context
		
		@param data: rendering data
		
		@return: the client connector rendering
		@rtype: ClientConnector
		"""
		yield defer.maybeDeferred(self.msg_service.connect)
		self.connector = ClientConnector(self.user_id, self.mind, self.msg_service, self.session_id)
		self.connector.setFragmentParent(self)
		defer.returnValue(ctx.tag[self.connector])

class ClientConnector(athena.LiveElement):
	"""
	Provides the AJAX communication channel with the server.
	"""
	# see antioch/assets/webroot/js/client.js
	jsClass = u'antioch.ClientConnector'
	docFactory = loaders.stan(tags.div(render=tags.directive('liveElement'))[
		tags.div(id='client-connector')
		])
	
	channel_counter = 0
	
	def __init__(self, user_id, mind, msg_service, session_id, *args, **kwargs):
		"""
		Setup the client connection.
		
		@param user_id: user ID of the logged-in player
		@type user_id: long
		
		@param mind: opaque object with ip_address and other info
		@type mind: C{Mind}
		
		@param msg_service: reference to the current process' message service
		@type msg_server: L{message.MessageService}
		
		@param session_id: user ID of the logged-in player
		@type session_id: long
		"""
		self.session_id = session_id
		self.user_id = user_id
		self.msg_service = msg_service
		
		def _init_eb():
			log.err()
			self.logout()
		
		self.login(mind).errback = _init_eb
		
		for mod in modules.iterate():
			if(hasattr(mod, 'activate_athena_commands')):
				mod.activate_athena_commands(self)
	
	@defer.inlineCallbacks
	def login(self, mind):
		"""
		Called when the user first connects, runs login verb code, 'look here'
		
		@param mind: opaque object with ip_address and other info
		@type mind: C{Mind}
		"""
		yield transact.Login.run(user_id=self.user_id, session_id=self.session_id, ip_address=mind.remote_host)
		
		self.chan = self.msg_service.setup_client_channel(self.user_id)
		self.queue = yield self.msg_service.connection.queue("user-%s-consumer" % self.user_id)
		
		yield transact.Parse.run(user_id=self.user_id, sentence='look here')
		
		self.loop = task.LoopingCall(self.queue_checker)
		self.loop.start(1.0)
	
	@defer.inlineCallbacks
	def logout(self, *args, **kwargs):
		"""
		Called when the twisted.cred Avatar goes away.
		"""
		self.loop.stop()
		
		if(hasattr(self, 'chan')):
			try:
				yield self.chan.basic_cancel("user-%s-consumer" % self.user_id)
				yield self.chan.channel_close()
			except:
				pass
		
		yield transact.Logout.run(user_id=self.user_id)
	
	@defer.inlineCallbacks
	def queue_checker(self):
		"""
		Continually called by the self.loop LoopingCall,
		this looks for messages sent to the user and
		processes them appropriately.
		"""
		try:
			msg = yield self.queue.get()
		except Closed, e:
			defer.returnValue(None)
		
		data = json.loads(msg.content.body.decode('utf8'))
		self.handle_message(data)
	
	def handle_message(self, data):
		"""
		Handle a single message from the RabbitMQ server.
		"""
		mod = modules.get(data['command'])
		
		if(mod):
			d = mod.handle_message(data, self)
		elif(data['command'] == 'task'):
			d = transact.RegisterTask(
						user_id=user_id, delay=data['delay'], origin_id=data['origin'], 
						verb_name=data['verb_name'], args=data['args'], kwargs=data['kwargs'])
		elif(data['command'] == 'observe'):
			# print 'setting observations for user #%s to %s' % (self.user_id, data['observations'])
			d = self.callRemote('setObservations', data['observations'])
		elif(data['command'] == 'write'):
			d = self.callRemote('write', data['text'], data['is_error'], data.get('escape_html', True))
	
	@defer.inlineCallbacks
	def task(self, task_id):
		"""
		Run a delayed task.
		"""
		yield transact.RunTask.run(user_id=self.user_id, task_id=task_id)
	
	@athena.expose	
	@defer.inlineCallbacks
	def parse(self, command):
		"""
		Parse a command sent by the client.
		"""
		yield transact.Parse.run(user_id=self.user_id, sentence=command.encode('utf8'))
