from django import template, shortcuts, http
from django.utils import simplejson
from django.conf import settings
from django.contrib.auth.decorators import login_required

from antioch import assets
from antioch.core import models
from antioch.plugins.editors import tasks

SUCCESS_JSON = '{"msg":"Successful update."}'
EXCEPTION_JSON = '{"msg":"%s"}'

def get_errors_json(form):
	return simplejson.dumps(dict(
		errors = form.errors,
		non_field_errors = form.non_field_errors
	))

class EditorFormView(object):
	def __init__(self, form_class, template):
		self.form_class = form_class
		self.template = template
	
	def as_view(self):
		def _view(request, object_id):
			o = models.Object.objects.get(pk=object_id)
	
			if(request.method == 'POST'):
				form = self.form_class(request.user.avatar.id, request.POST, instance=o)
				if(form.is_valid()):
					try:
						form.save()
						return http.HttpResponse(SUCCESS_JSON, content_type="application/json")
					except Exception, e:
						return http.HttpResponse(EXCEPTION_JSON % e, content_type="application/json", status=500)
				else:
					return http.HttpResponse(get_errors_json(form.errors), content_type="application/json", status=422)
			else:
				form = self.form_class(request.user.avatar.id, instance=o)
	
			return shortcuts.render_to_response(self.template, dict(form=form), context_instance=template.RequestContext(request))
		return login_required(_view)

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

