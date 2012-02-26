# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

from ajax_select import LookupChannel
from django.utils.html import escape
from django.db.models import Q

from antioch.client import models

class ObjectLookup(LookupChannel):
	model = models.Object
	
	def check_auth(self, request):
		return request.user.is_authenticated()
	
	def get_query(self, q, request):
		return models.Object.objects.filter(name__istartswith=q).order_by('name')
	
	def get_result(self, obj):
		"""result is the simple text that is the completion of what the person typed """
		return obj.name
	
	def format_match(self, obj):
		""" (HTML) formatted item for display in the dropdown """
		return escape(obj.name)
	
	def format_item_display(self,obj):
		""" (HTML) formatted item for displaying item in the selected deck area """
		return escape(unicode(obj))