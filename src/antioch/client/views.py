from django import template, shortcuts
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required

from antioch import plugins

@login_required
def client(request):
	return shortcuts.render_to_response('client.html', dict(
		title           = "antioch client",
		scripts         = [p.script_url for p in plugins.iterate() if p],
	), context_instance=template.RequestContext(request))

def logout(request):
	auth.logout(request)
	return shortcuts.redirect('client')
