from django.urls import include, path

from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'objects', views.ObjectViewSet)
router.register(r'relationships', views.RelationshipViewSet)
router.register(r'observations', views.ObservationViewSet)
router.register(r'aliases', views.AliasViewSet)
router.register(r'verbs', views.VerbViewSet)
router.register(r'verbNames', views.VerbNameViewSet)
router.register(r'properties', views.PropertyViewSet)
router.register(r'acls', views.AccessViewSet)
router.register(r'players', views.PlayerViewSet)
router.register(r'tasks', views.TaskViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
