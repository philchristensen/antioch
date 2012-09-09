# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

from itertools import chain

from django.conf import settings
from django.forms import widgets

class LessMedia(widgets.Media):
	"""
	A subclass of the Django Media class supporting LESS CSS (lesscss.org).
	"""
	def __init__(self, media=None, **kwargs):
		"""
		Create a new LessMedia instance.
		"""
		if('less' not in widgets.MEDIA_TYPES):
			# Django doesn't make it easy for us to subclass Media,
			# so we have to monkeypatch the old Media class to ignore
			# the extra entry in MEDIA_TYPES
			widgets.MEDIA_TYPES = ('less',) + widgets.MEDIA_TYPES
			widgets.Media.add_less = lambda *args: None
			widgets.Media.render_less = lambda *args: []
		self._less = {}
		widgets.Media.__init__(self, media, **kwargs)

	def add_less(self, data):
		"""
		Add less files to the internal list.
		"""
		if data:
			for medium, paths in data.items():
				for path in paths:
					if not self._less.get(medium) or path not in self._less[medium]:
						self._less.setdefault(medium, []).append(path)

	def render_less(self):
		"""
		Output the necessary media tags, including LESS support scripts (when necessary)
		"""
		media = self._less.keys()
		media.sort()
		if(settings.RENDER_LESS):
			# If RENDER_LESS is true, also add the JS interpreter
			# This only works because 'javascript' comes before 'less' in MEDIA_TYPES.
			if(media):
				self.add_js(('%sjs/less-1.3.0.min.js' % settings.STATIC_URL,))
			return chain(*[
				[u'<link href="%(href)s" type="text/css" media="%(medium)s" rel="stylesheet/less">' % dict(
					href    = self.absolute_path(path),
					medium  = medium,
				) for path in self._less[medium]]
			for medium in media])
		else:
			# if RENDER_LESS is false, then we assume that there's a .css file
			# next to the .less file, and attempt to include that
			return chain(*[
				[u'<link href="%(href)s" type="text/css" media="%(medium)s" rel="stylesheet" />' % dict(
					href    = self.absolute_path(path.replace('.less', '.css')),
					medium  = medium,
				) for path in self._less[medium]]
			for medium in media])

	def __add__(self, other):
		"""
		When you concatenate a LessMedia to another media object, you always get back a LessMedia object.
		"""
		combined = LessMedia()
		for name in widgets.MEDIA_TYPES:
			getattr(combined, 'add_' + name)(getattr(self, '_' + name, None))
			getattr(combined, 'add_' + name)(getattr(other, '_' + name, None))
		return combined
