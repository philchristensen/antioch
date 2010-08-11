class ConnectionWrapper:
	def __init__(self, connection):
		self.connection = connection
		self.client_type = self.get_type()
	
	def get_type(self):
		from txspace.client import web
		
		if(isinstance(self.connection, web.ClientConnector)):
			return 'web'
			
	def set_observations(self, observations):
		if(observations is None):
			raise ValueError, "Cannot set null observations."
		if(self.get_type() == 'web'):
			return self.connection.callRemote('setObservations', observations)
	
	def write(self, text, is_error=False):
		if(self.get_type() == 'web'):
			if(isinstance(text, str)):
				text = text.decode('utf-8')
			return self.connection.callRemote('write', text, is_error)
	
	def open_editor(self, editor, info):
		if(self.get_type() == 'web'):
			return self.connection.callRemote(editor + 'edit', info)
	
	def logout(self):
		if(self.get_type() == 'web'):
			return self.connection.callRemote('logout')


