from django import template, shortcuts
from django.conf import settings
from django.contrib.auth.decorators import login_required

from antioch.core import appserver
from antioch.client import models
from antioch.plugins.editors import forms

@login_required
def object_editor(request, object_id):
	o = models.Object.objects.get(pk=object_id)
	
	if(request.method == 'POST'):
		form = forms.ObjectForm(request.POST, instance=o)
		if(form.is_valid()):
			appserver.run('modify-object',
				user_id		= request.user.avatar.id,
				object_id	= o.id,
				name		= form.cleaned_data['name'],
				location	= request.POST['location'],
				owner		= request.POST['owner'],
				parents		= request.POST['parents'].replace('|', ',').strip(','),
			)
	else:
		form = forms.ObjectForm(instance=o)
	
	return shortcuts.render_to_response('object-editor.html', dict(
		title           = "object editor",
		form            = form,
	), context_instance=template.RequestContext(request))

@login_required
def property_editor(request, property_id):
	p = models.Property.objects.get(pk=property_id)
	
	if(request.method == 'POST'):
		form = forms.PropertyForm(request.POST, instance=p)
		if(form.is_valid()):
			appserver.run('modify-property',
				user_id		= request.user.avatar.id,
				object_id	= str(p.origin.id),
				property_id	= str(p.id),
				name		= form.cleaned_data['name'],
				value		= form.cleaned_data['value'],
				type		= form.cleaned_data['type'],
				owner		= request.POST['owner'],
			)
	else:
		form = forms.PropertyForm(instance=p)
	
	return shortcuts.render_to_response('property-editor.html', dict(
		title           = "property editor",
		form            = form,
	), context_instance=template.RequestContext(request))

@login_required
def verb_editor(request, verb_id):
	return shortcuts.render_to_response('verb-editor.html', dict(
		title           = "verb editor",
	), context_instance=template.RequestContext(request))

@login_required
def access_editor(request, entity_type, entity_id):
	return shortcuts.render_to_response('access-editor.html', dict(
		title           = "access editor",
	), context_instance=template.RequestContext(request))

