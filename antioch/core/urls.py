from django.urls import include, path

from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'objects', views.ObjectViewSet)
router.register(r'verbs', views.VerbViewSet)
router.register(r'properties', views.PropertyViewSet)
router.register(r'acls', views.AccessViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
