from django.conf.urls import include, url

from antioch.plugins.editors import views

app_name = 'editors'

urlpatterns = [
    url(r'^editor/object/(?P<pk>\d+)', views.ObjectEditorFormView.as_view(), name='object_editor'),
    url(r'^editor/property/(?P<pk>\d+)', views.PropertyEditorFormView.as_view(), name='property_editor'),
    url(r'^editor/verb/(?P<pk>\d+)', views.VerbEditorFormView.as_view(), name='verb_editor'),
    url(r'^editor/access/(?P<type>object|verb|property)/(?P<pk>\d+)', views.AccessEditorFormView.as_view(), name='access_editor'),
]