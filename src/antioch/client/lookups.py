# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Endpoints for AJAX field lookups.
"""

from ajax_select import LookupChannel
from django.utils.html import escape
from django.db.models import Q

from antioch.client import models

class ObjectLookup(LookupChannel):
	"""
	Lookup an object by name.
	"""
	model = models.Object
	
	def check_auth(self, request):
		"""
		All users have access.
		"""
		return request.user.is_authenticated()
	
	def get_query(self, q, request):
		"""
		Get the matching results.
		"""
		return models.Object.objects.filter(name__istartswith=q).order_by('name')
	
	def get_result(self, obj):
		"""
		Returns the completion of what was queried.
		"""
		return obj.name
	
	def format_match(self, obj):
		"""
		HTML formatted item for display in the dropdown
		"""
		return escape(obj.name)
	
	def format_item_display(self,obj):
		"""
		HTML formatted item for displaying item in the selected deck area
		"""
		return escape(unicode(obj))