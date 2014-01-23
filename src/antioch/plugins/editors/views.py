from django import template, shortcuts, http
from django.utils import simplejson
from django.conf import settings
from django.contrib.auth.decorators import login_required

from antioch import assets
from antioch.core import models
from antioch.plugins.editors import forms, tasks

@login_required
def object_editor(request, object_id):
	o = models.Object.objects.get(pk=object_id)
	
	if(request.method == 'POST'):
		form = forms.ObjectForm(request.POST, instance=o)
		if(form.is_valid()):
			tasks.modifyobject.delay(
				user_id		= request.user.avatar.id,
				object_id	= o.id,
				name		= form.cleaned_data['name'],
				location	= request.POST['location'],
				owner		= request.POST['owner'],
				parents		= request.POST['parents'].replace('|', ',').strip(','),
			).get(timeout=5)
			return http.HttpResponse("Successful update.")
		else:
			return http.HttpResponse(simplejson.dumps(form.errors), content_type="application/json", status=422)
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
			tasks.modifyproperty.delay(
				user_id		= request.user.avatar.id,
				object_id	= str(p.origin.id),
				property_id	= str(p.id),
				name		= form.cleaned_data['name'],
				value		= form.cleaned_data['value'],
				type		= form.cleaned_data['type'],
				owner		= request.POST['owner'],
			).get(timeout=5)
	else:
		form = forms.PropertyForm(instance=p)
	
	return shortcuts.render_to_response('property-editor.html', dict(
		title           = "property editor",
		form            = form,
	), context_instance=template.RequestContext(request))

@login_required
def verb_editor(request, verb_id):
	v = models.Verb.objects.get(pk=verb_id)
	names = ', '.join([n.name for n in v.names.all()])
	
	if(request.method == 'POST'):
		form = forms.VerbForm(request.POST, instance=v, initial=dict(names=names))
		if(form.is_valid()):
			tasks.modifyverb.delay(
				user_id		= request.user.avatar.id,
				object_id	= str(v.origin.id),
				verb_id		= str(v.id),
				names		= form.cleaned_data['names'],
				code		= form.cleaned_data['code'],
				ability		= form.cleaned_data['ability'],
				method		= form.cleaned_data['method'],
				owner		= request.POST['owner'],
			).get(timeout=5)
	else:
		form = forms.VerbForm(instance=v, initial=dict(names=names))
	
	return shortcuts.render_to_response('verb-editor.html', dict(
		title           = "verb editor",
		form            = form,
	), context_instance=template.RequestContext(request))

@login_required
def access_editor(request, type, pk):
	if type not in ('verb', 'property', 'object'):
		raise http.Http404()
	
	Model = getattr(models, type.capitalize())
	m = Model.objects.get(pk=pk)
	
	if(request.method == 'POST'):
		print request.POST
		acl = []
		for key in request.POST:
			if not key.startswith('accessid-'):
				continue
			access_id = request.POST[key]
			acl.append(dict(
				access_id	= int(access_id),
				deleted		= bool(int(request.POST['deleted-%s' % access_id])),
				rule		= request.POST['rule-%s' % access_id],
				access		= request.POST['access-%s' % access_id],
				accessor	= request.POST['accessor-%s' % access_id],
				permission	= request.POST['permission-%s' % access_id],
				weight		= int(request.POST['weight-%s' % access_id]),
			))
		
		tasks.modifyaccess.delay(
			user_id		= request.user.avatar.id,
			object_id	= str(model.id),
			type		= type,
			access		= acl,
		).get(timeout=5)
	
	return shortcuts.render_to_response('access-editor.html', dict(
		title           = "access editor",
		model           = m,
	), context_instance=template.RequestContext(request))

