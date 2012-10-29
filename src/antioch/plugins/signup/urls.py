from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('registration.views',
	url(r'^activate/complete/$',
		direct_to_template,
		{'template': 'registration/activation_complete.html'},
		name='registration_activation_complete'),
	# Activation keys get matched by \w+ instead of the more specific
	# [a-fA-F0-9]{40} because a bad activation key should still get to the view;
	# that way it can return a sensible "invalid key" message instead of a
	# confusing 404.
	url(r'^activate/(?P<activation_key>\w+)/$',
		'activate',
		{'backend': 'antioch.plugins.registration.RegistrationBackend'},
		name='registration_activate'),
	url(r'^register/$',
		'register',
		{'backend': 'antioch.plugins.registration.RegistrationBackend'},
		name='registration_register'),
	url(r'^register/complete/$',
		direct_to_template,
		{'template': 'registration/registration_complete.html'},
		name='registration_complete'),
	url(r'^register/closed/$',
		direct_to_template,
		{'template': 'registration/registration_closed.html'},
		name='registration_disallowed'),
)
