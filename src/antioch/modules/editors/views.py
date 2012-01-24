from django import template, shortcuts
from django.conf import settings
from django.contrib.auth.decorators import login_required

from antioch import modules

@login_required
def object_editor(request):
	return shortcuts.render_to_response('object-editor.html', dict(
		title           = "object editor",
	), context_instance=template.RequestContext(request))

@login_required
def property_editor(request):
	return shortcuts.render_to_response('property-editor.html', dict(
		title           = "property editor",
	), context_instance=template.RequestContext(request))

@login_required
def verb_editor(request):
	return shortcuts.render_to_response('verb-editor.html', dict(
		title           = "verb editor",
	), context_instance=template.RequestContext(request))

@login_required
def access_editor(request):
	return shortcuts.render_to_response('access-editor.html', dict(
		title           = "access editor",
	), context_instance=template.RequestContext(request))

