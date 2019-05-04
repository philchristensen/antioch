from rest_framework import viewsets

from . import models, serializers

class ObjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows objects to be viewed or edited.
    """
    queryset = models.Object.objects.all()
    serializer_class = serializers.ObjectSerializer

class RelationshipViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows relationships to be viewed or edited.
    """
    queryset = models.Relationship.objects.all()
    serializer_class = serializers.RelationshipSerializer

class VerbViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows verbs to be viewed or edited.
    """
    queryset = models.Verb.objects.all()
    serializer_class = serializers.VerbSerializer

class PropertyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows propertys to be viewed or edited.
    """
    queryset = models.Property.objects.all()
    serializer_class = serializers.PropertySerializer

class AccessViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows access rules to be viewed or edited.
    """
    queryset = models.Access.objects.all()
    serializer_class = serializers.AccessSerializer
