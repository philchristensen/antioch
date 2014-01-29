from django import template, shortcuts, http
from django.utils import simplejson
from django.conf import settings
from django.views.generic import UpdateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.forms.models import modelformset_factory

from antioch import assets
from antioch.core import models
from antioch.plugins.editors import tasks, forms

SUCCESS_JSON = '{"msg":"Successful update."}'
EXCEPTION_JSON = '{"msg":"%s"}'

def get_errors_json(form):
	return simplejson.dumps(dict(
		errors = form.errors,
		non_field_errors = form.non_field_errors
	))

class LoginRequiredMixin(object):
	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(LoginRequiredMixin, self).dispatch(*args, **kwargs) 

class AjaxFormMixin(object):
	def form_valid(self, form):
		try:
			form.save()
			return http.HttpResponse(SUCCESS_JSON, content_type="application/json")
		except Exception, e:
			return http.HttpResponse(EXCEPTION_JSON % e, content_type="application/json", status=500)
	
	def form_invalid(self, form):
		return http.HttpResponse(get_errors_json(form.errors), content_type="application/json", status=422)

class EditorFormView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
	def get_form_kwargs(self):
		kwargs = super(EditorFormView, self).get_form_kwargs()
		kwargs['user_id'] = self.request.user.avatar.id
		return kwargs
	
class ObjectEditorFormView(EditorFormView):
	template_name = 'object-editor.html'
	form_class = forms.ObjectForm
	model = models.Object
	
class PropertyEditorFormView(EditorFormView):
	template_name = 'property-editor.html'
	form_class = forms.PropertyForm
	model = models.Property
	
class VerbEditorFormView(EditorFormView):
	template_name = 'verb-editor.html'
	form_class = forms.VerbForm
	model = models.Verb

class AccessEditorFormView(LoginRequiredMixin, AjaxFormMixin, UpdateView):
	template_name = 'access-editor.html'
	form_class = modelformset_factory(models.Access, extra=0, form=forms.AccessForm)
	model = models.Access
	
	def get_form_kwargs(self):
		kwargs = dict()
		kwargs['queryset'] = self.model.objects.filter(**{'%s__pk' % self.kwargs['type']: self.kwargs['pk']})
		return kwargs

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

