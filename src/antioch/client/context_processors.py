"""
Add some essential variables to the template environment.
"""

from django.conf import settings

def default_variables(request):
	"""
	Adds default context variables to the template.
	"""
	return {
		'JQUERY_VERSION': settings.JQUERY_VERSION,
		'JQUERY_UI_VERSION': settings.JQUERY_UI_VERSION,
	}

