# txSpace
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import simplejson

from twisted.protocols import amp

from txspace import transact

class AnswerQuestion(transact.WorldTransaction):
	arguments = [
		('user_id', amp.Integer()),
		('object_id', amp.Integer()),
		('method_name', amp.String()),
		('response', amp.String()),
		('args', amp.String()),
		('kwargs', amp.String()),
	]

class AskTransactionChild(transact.TransactionChild):
	@AnswerQuestion.responder
	def answer_question(self, user_id, object_id, method_name, response, args, kwargs):
		args = simplejson.loads(args)
		kwargs = simplejson.loads(kwargs)
		try:
			with self.get_exchange(user_id) as x:
				obj = x.get_object(object_id)
				method = obj.get_verb(method_name)
				method(response, *args, **kwargs)
		except Exception, e:
			print e
		return {'response': True}
	
