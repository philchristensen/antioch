from django import template, shortcuts
from django.conf import settings
from django.contrib.auth.decorators import login_required

from antioch import modules

@login_required
def object_editor(request):
	return shortcuts.render_to_response('object-editor.html', dict(
		title           = "object editor",
	), context_instance=template.RequestContext(request))

