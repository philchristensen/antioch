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

class ObservationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows observations to be viewed or edited.
    """
    queryset = models.Observation.objects.all()
    serializer_class = serializers.ObservationSerializer

class AliasViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows aliass to be viewed or edited.
    """
    queryset = models.Alias.objects.all()
    serializer_class = serializers.AliasSerializer

class VerbViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows verbs to be viewed or edited.
    """
    queryset = models.Verb.objects.all()
    serializer_class = serializers.VerbSerializer

class VerbNameViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows verbnames to be viewed or edited.
    """
    queryset = models.VerbName.objects.all()
    serializer_class = serializers.VerbNameSerializer

class PropertyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows propertys to be viewed or edited.
    """
    queryset = models.Property.objects.all()
    serializer_class = serializers.PropertySerializer

class AccessViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows accesss to be viewed or edited.
    """
    queryset = models.Access.objects.all()
    serializer_class = serializers.AccessSerializer

class PlayerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows players to be viewed or edited.
    """
    queryset = models.Player.objects.all()
    serializer_class = serializers.PlayerSerializer

class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows tasks to be viewed or edited.
    """
    queryset = models.Task.objects.all()
    serializer_class = serializers.TaskSerializer

