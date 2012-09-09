# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

"""
Add some essential variables to the template environment.
"""

from django.conf import settings

from antioch import assets

def default_variables(request):
	"""
	Adds default context variables to the template.
	"""
	return {
		'JQUERY_VERSION': settings.JQUERY_VERSION,
		'JQUERY_UI_VERSION': settings.JQUERY_UI_VERSION,
		'LOGIN_MEDIA': assets.LessMedia(
			less        = dict(
				screen  = [
					'%sless/client-login.less' % settings.STATIC_URL,
				],
			),
		),
		'BOOTSTRAP_MEDIA': assets.LessMedia(
			less        = dict(
				screen  = [
					'%sbootstrap/less/bootstrap.less' % settings.STATIC_URL,
					'%sbootstrap/less/responsive.less' % settings.STATIC_URL,
				],
			),
		),
	}

