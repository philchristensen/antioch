import httplib, urlparse, urllib, urllib2, os.path

from django import template, shortcuts, http
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt

import simplejson

from antioch import plugins

@login_required
def client(request):
	return shortcuts.render_to_response('client.html', dict(
		title           = "antioch client",
		scripts         = [p.script_url for p in plugins.iterate() if p],
	), context_instance=template.RequestContext(request))

@login_required
def comet(request):
	url = urlparse.urlparse(settings.APPSERVER_URL)
	conn = httplib.HTTPConnection(url.netloc)
	conn.request('GET', '/comet/%d' % request.user.avatar.id)
	response = conn.getresponse()
	def _reader():
		g = iter(response.read, '')
		try:
			yield g.next()
		except StopIteration:
			conn.close()
	return http.HttpResponse(_reader(), content_type="application/json")

@login_required
@csrf_exempt
def rest(request, command):
	data = simplejson.loads(request.read())
	data['user_id'] = request.user.avatar.id
	return http.HttpResponse(urllib2.urlopen(
		os.path.join(settings.APPSERVER_URL, 'rest', command),
		simplejson.dumps(data)
	), content_type="application/json")

def logout(request):
	auth.logout(request)
	return shortcuts.redirect('client')
