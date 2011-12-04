# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

from twisted.internet import defer

from antioch.util import json
from antioch.modules.editors import transactions

class EditorRemoteReference(object):
	def req_object_editor(self, object_id):
		"""
		Open an object editor as requested by the client.
		"""
		return transactions.OpenEditor.run(
			transaction_child	= transactions.EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= 'object',
			name		= '',
		)
	
	def req_verb_editor(self, object_id, verb_name):
		"""
		Open a verb editor as requested by the client.
		"""
		return transactions.OpenEditor.run(
			transaction_child	= transactions.EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= 'verb',
			name		= verb_name.encode('utf8'),
		)
	
	def req_property_editor(self, object_id, property_name):
		"""
		Open a property editor as requested by the client.
		"""
		return transactions.OpenEditor.run(
			transaction_child	= transactions.EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= 'property',
			name		= property_name.encode('utf8'),
		)
	
	def req_access_editor(self, object_id, type, name):
		"""
		Open an access editor as requested by the client.
		"""
		return transactions.OpenAccess.run(
			transaction_child	= transactions.EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			type		= type.encode('utf8'),
			name		= name.encode('utf8'),
		)
	
	@defer.inlineCallbacks
	def get_object_details(self, object_id):
		"""
		Return object details (id, attributes, verbs, properties).
		"""
		result = yield transactions.GetObjectDetails.run(
			transaction_child	= transactions.EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
		)
		result = json.loads(json.dumps(result).decode('utf8'))
		defer.returnValue(result)
	
	def remove_verb(self, object_id, verb_name):
		"""
		Attempt to remove a verb from an object.
		"""
		return transactions.RemoveVerb.run(
			transaction_child	= transactions.EditorTransactionChild,
			user_id		= self.user_id,
			object_id	= unicode(object_id).encode('utf8'),
			verb_name	= verb_name.encode('utf8'),
		)
	
	def remove_property(self, object_id, property_name):
		"""
		Attempt to remove a property from an object.
		"""
		return transactions.RemoveProperty.run(
			transaction_child	= transactions.EditorTransactionChild,
			user_id			= self.user_id,
			object_id		= unicode(object_id).encode('utf8'),
			property_name	= property_name.encode('utf8'),
		)