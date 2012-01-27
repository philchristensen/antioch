from django import template, shortcuts
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required

from antioch import modules

@login_required
def client(request):
	return shortcuts.render_to_response('client.html', dict(
		title           = "antioch client",
		plugins         = [m.script_url for m in modules.iterate() if m],
	), context_instance=template.RequestContext(request))

def logout(request):
	auth.logout(request)
	return shortcuts.redirect('client')
