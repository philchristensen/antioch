# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

"""
Webclient


This is the primary client for txSpace, replacing the
Java and Cocoa versions.
"""
import os, os.path

from zope.interface import implements

import simplejson

from twisted.application import service, internet
from twisted.internet import reactor, defer, task
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.cred import credentials
from twisted.python import failure, log

from nevow import inevow, loaders, athena, guard, rend, tags

from txamqp import content
from txamqp.queue import Closed

from txspace import errors, assets, transact, session

def createTemplatePage(template):
	className = ''.join([x.capitalize() for x in os.path.basename(template).split('-')])
	return type(className, (rend.Page,), dict(docFactory=loaders.xmlfile(template)))

ObjectEditor = createTemplatePage(assets.get_template_path('object-editor'))
VerbEditor = createTemplatePage(assets.get_template_path('verb-editor'))
PropertyEditor = createTemplatePage(assets.get_template_path('property-editor'))
AccessEditor = createTemplatePage(assets.get_template_path('access-editor'))

class Mind(object):
	"""
	Represents a client connection.
	"""
	def __init__(self, request, credentials):
		"""
		Hold on to IP address info for the client.
		"""
		self.addr = request.transport.client
		self.remote_host = self.addr[0]


class RootDelegatePage(rend.Page):
	login_url = '/login'
	logout_url = '/logout'
	client_url = '/universe'
	
	def __init__(self, pool, msg_service, portal):
		"""
		Create a new root delegate page connected to the given pool and portal.
		
		@param pool: the current session store
		@type pool: L{txspace.client.web.session.IUserSessionStore}
		
		@param portal: the current auth portal
		@param portal: L{twisted.cred.portal.Portal}
		"""
		self.pool = pool
		self.portal = portal
		self.msg_service = msg_service
		self.connections = {}
		
		assets.enable_assets(self)
	
	@inlineCallbacks
	def locateChild(self, ctx, segments):
		"""
		Take care of authentication while returning Resources or redirecting.
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
						client = self.connections[sid] = ClientInterface(user, mind, self.msg_service)
					returnValue((client, segments[1:]))
				elif(len(segments) > 1 and segments[0] == 'edit'):
					if(segments[1] == 'object'):
						returnValue((ObjectEditor(user), segments[2:]))
					elif(segments[1] == 'verb'):
						returnValue((VerbEditor(user), segments[2:]))
					elif(segments[1] == 'property'):
						returnValue((PropertyEditor(user), segments[2:]))
					elif(segments[1] == 'access'):
						returnValue((AccessEditor(user), segments[2:]))
				elif(segments[0] == 'logout'):
					self.pool.logoutUser(sid)
					if(sid in self.connections):
						del self.connections[sid]
					request = inevow.IRequest(ctx)
					request.redirect('/login')
					returnValue((ClientLogin(self.pool, self.portal), segments[1:]))
			# not logged in, at login page
			elif(segments[0] == 'login'):
				returnValue((ClientLogin(self.pool, self.portal), segments[1:]))
			# usually because server restarted or was bookmarked
			# redirect to the login page for convenience
			elif(segments[0] in ('logout', 'universe')):
				request = inevow.IRequest(ctx)
				request.redirect('/login')
				returnValue((ClientLogin(self.pool, self.portal), segments[1:]))
		
		# let renderHTTP take care of the redirect to /login or /universe
		returnValue(super(RootDelegatePage, self).locateChild(ctx, segments))
	
	@inlineCallbacks
	def renderHTTP(self, ctx):
		"""
		Redirect either to the client interface or a login form.
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
		"""
		request = inevow.IRequest(ctx)

		creds = session.getSessionCredentials(ctx)
		iface, user, logout = yield self.portal.login(creds, None, inevow.IResource)
		yield session.updateSession(self.pool, request, user)
		
		if(session.ISessionCredentials.providedBy(creds)):
			sid = creds.getSid()
		else:
			sid = None
		
		returnValue((user, sid))
	
	@inlineCallbacks
	def authRedirect(self, ctx):
		"""
		Authenticate the current session, redirecting to login if necessary.
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
	
	def __init__(self, pool, portal):
		"""
		Provide the necessary objects to handle session saving.
		"""
		super(ClientLogin, self).__init__()
		self.docFactory = loaders.xmlfile(assets.get_template_path('client-login'))
		self.portal = portal
		self.pool = pool
	
	@inlineCallbacks	
	def renderHTTP(self, ctx):
		"""
		Present the login form and handle login on POST.
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
			yield session.updateSession(self.pool, request, user)
			
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
	
	def __init__(self, user, mind, msg_service):
		"""
		Setup the client interface.
		"""
		super(ClientInterface, self).__init__()
		
		self.msg_service = msg_service
		
		self.user_id = user['avatar_id']
		self.mind = mind
		self.docFactory = loaders.xmlfile(assets.get_template_path('client'))
		self.connector = None
		self.notifyOnDisconnect().errback = self.logout
	
	def logout(self, *args, **kwargs):
		if(self.connector):
			self.connector.logout(*args, **kwargs)
		else:
			raise RuntimeError("Logout called before LiveElement was rendered.")
	
	@defer.inlineCallbacks
	def render_ClientConnector(self, ctx, data):
		"""
		Render the Athena connection element.
		"""
		yield defer.maybeDeferred(self.msg_service.connect)
		self.connector = ClientConnector(self.user_id, self.mind, self.msg_service)
		self.connector.setFragmentParent(self)
		defer.returnValue(ctx.tag[self.connector])

class ClientConnector(athena.LiveElement):
	"""
	Provides the AJAX communication channel with the server.
	"""
	# see txspace/assets/webroot/js/client.js
	jsClass = u'txspace.ClientConnector'
	docFactory = loaders.stan(tags.div(render=tags.directive('liveElement'))[
		tags.div(id='client-connector')
		])
	
	channel_counter = 0
	
	def __init__(self, user_id, mind, msg_service, *args, **kwargs):
		"""
		Setup the client connection.
		"""
		self.user_id = user_id
		self.msg_service = msg_service
		
		def _init_eb():
			log.err()
			self.logout()
		
		self.login(mind).errback = _init_eb
	
	@defer.inlineCallbacks
	def login(self, mind):
		yield transact.Login.run(user_id=self.user_id, ip_address=mind.remote_host)
		
		self.chan = yield self.msg_service.open_channel()
		
		exchange = 'user-exchange'
		queue = 'user-%s-queue' % self.user_id
		consumertag = "user-%s-consumer" % self.user_id
		routing_key = 'user-%s' % self.user_id
		
		yield self.chan.exchange_declare(exchange=exchange, type="direct", durable=False, auto_delete=True)
		yield self.chan.queue_declare(queue=queue, durable=False, exclusive=False, auto_delete=True)
		yield self.chan.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)
		yield self.chan.basic_consume(queue=queue, no_ack=True, consumer_tag=consumertag)
		
		self.queue = yield self.msg_service.connection.queue(consumertag)
		
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
		try:
			msg = yield self.queue.get()
		except Closed, e:
			defer.returnValue(None)
		
		data = simplejson.loads(msg.content.body.decode('utf8'))
		
		if(data['command'] == 'observe'):
			d = self.callRemote('setObservations', data['observations'])
		elif(data['command'] == 'write'):
			d = self.callRemote('write', data['text'], data['is_error'])
		elif(data['command'] == 'access'):
			def _cb_accessedit(result):
				return transact.ModifyAccess.run(
					user_id		= self.user_id,
					object_id	= str(data['details']['id']),
					type		= data['details']['type'].encode('utf8'),
					access		= [dict(
						access_id	= int(access_id),
						deleted		= item['deleted'],
						rule		= item['rule'].encode('utf8'),
						access		= item['access'].encode('utf8'),
						accessor	= item['accessor'].encode('utf8'),
						permission	= item['permission'].encode('utf8'),
						weight		= item['weight'],
					) for access_id, item in result['access'].items()]
				) if result else None
			d = self.callRemote('accessedit', data['details'])
			d.addCallback(_cb_accessedit)
		elif(data['command'] == 'edit'):
			if(data['details']['kind'] == 'object'):
				def _cb_objedit(result):
					return transact.ModifyObject.run(
						user_id		= self.user_id,
						object_id	= data['details']['id'],
						name		= result['name'].encode('utf8'),
						location	= result['location'].encode('utf8'),
						parents		= result['parents'].encode('utf8'),
						owner		= result['owner'].encode('utf8'),
					) if result else None
				d = self.callRemote('objedit', data['details'])
				d.addCallback(_cb_objedit)
			elif(data['details']['kind'] == 'property'):
				def _cb_propedit(result):
					return transact.ModifyProperty.run(
						user_id		= self.user_id,
						object_id	= data['details']['origin'].encode('utf8'),
						property_id	= str(data['details']['id']),
						name		= result['name'].encode('utf8'),
						value		= result['value'].encode('utf8'),
						type		= str(result['type']),
						owner		= result['owner'].encode('utf8'),
					) if result else None
				d = self.callRemote('propedit', data['details'])
				d.addCallback(_cb_propedit)
			elif(data['details']['kind'] == 'verb'):
				def _cb_verbedit(result):
					return transact.ModifyVerb.run(
						user_id		= self.user_id,
						object_id	= data['details']['origin'].encode('utf8'),
						verb_id		= str(data['details']['id']),
						names		= result['names'].encode('utf8'),
						code		= result['code'].encode('utf8'),
						exec_type	= result['exec_type'].encode('utf8'),
						owner		= result['owner'].encode('utf8'),
					) if result else None
				d = self.callRemote('verbedit', data['details'])
				d.addCallback(_cb_verbedit)
	
	@athena.expose	
	@defer.inlineCallbacks
	def parse(self, command):
		"""
		Parse a command sent by the client.
		"""
		yield transact.Parse.run(user_id=self.user_id, sentence=command.encode('utf8'))
	
	@athena.expose	
	@defer.inlineCallbacks
	def req_object_editor(self, object_id):
		"""
		Open an object editor as requested by the client.
		"""
		yield transact.OpenEditor.run(
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= 'object',
			name		= '',
		)
	
	@athena.expose	
	@defer.inlineCallbacks
	def req_verb_editor(self, object_id, verb_name):
		"""
		Open a verb editor as requested by the client.
		"""
		yield transact.OpenEditor.run(
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= 'verb',
			name		= verb_name.encode('utf8'),
		)
	
	@athena.expose	
	@defer.inlineCallbacks
	def req_property_editor(self, object_id, property_name):
		"""
		Open a property editor as requested by the client.
		"""
		yield transact.OpenEditor.run(
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= 'property',
			name		= property_name.encode('utf8'),
		)
	
	@athena.expose	
	@defer.inlineCallbacks
	def req_access_editor(self, object_id, type, name):
		"""
		Open an access editor as requested by the client.
		"""
		yield transact.OpenAccess.run(
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= type.encode('utf8'),
			name		= name.encode('utf8'),
		)
	
	@athena.expose	
	@defer.inlineCallbacks
	def get_object_details(self, object_id):
		"""
		Return object details (id, attributes, verbs, properties).
		"""
		result = yield transact.GetObjectDetails.run(
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
		)
		result = simplejson.loads(simplejson.dumps(result).decode('utf8'))
		defer.returnValue(result)
	
	@athena.expose	
	def remove_verb(self, id, verb_name):
		"""
		Attempt to remove a verb from an object.
		"""
		obj = self.registry.get(id)
		return obj.remove_verb(self.user, verb_name)
	
	@athena.expose	
	def remove_property(self, id, property_name):
		"""
		Attempt to remove a property from an object.
		"""
		obj = self.registry.get(id)
		return obj.remove_property(self.user, property_name)

