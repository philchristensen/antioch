from django import template, shortcuts
from django.contrib.auth.decorators import login_required
from django.contrib import auth

@login_required
def client(request):

	return shortcuts.render_to_response('client.html', dict(
		title           = "antioch client",
	), context_instance=template.RequestContext(request))

def logout(request):
	auth.logout(request)
	return shortcuts.redirect('client')