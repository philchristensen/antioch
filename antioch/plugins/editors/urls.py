from django.urls import include, path

from antioch.plugins.editors import views

app_name = 'editors'

urlpatterns = [
    path(r'editor/object/<int:pk>', views.ObjectEditorFormView.as_view(), name='object_editor'),
    path(r'editor/property/<int:pk>', views.PropertyEditorFormView.as_view(), name='property_editor'),
    path(r'editor/verb/<int:pk>', views.VerbEditorFormView.as_view(), name='verb_editor'),
    path(r'editor/access/<slug:type>/<int:pk>', views.AccessEditorFormView.as_view(), name='access_editor'),
]