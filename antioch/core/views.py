from django.shortcuts import get_object_or_404
from django.db import connection

from rest_framework import viewsets, response, exceptions
from rest_framework.decorators import action

from . import models, serializers, exchange

class ObjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows objects to be viewed or edited.
    """
    serializer_class = serializers.ObjectSerializer

    def get_queryset(self):
        if(self.request.GET):
            ex = exchange.ObjectExchange(connection, ctx=self.request.user.avatar.pk)
            queryset = models.Object.objects.filter(id__in=self.request.GET.getlist('id'))
            for obj in queryset:
                user = ex.get_object(self.request.user.avatar.pk)
                obj = ex.get_object(obj.pk)
                ex.is_allowed(user, 'read', obj)
            return queryset
        elif('pk' in self.request.parser_context['kwargs']):
            return models.Object.objects.filter(pk=self.request.parser_context['kwargs']['pk'])
        else:
            return models.Object.objects.filter(location=self.request.user.avatar.location)
    
    @action(detail=True, methods=['post', 'put', 'patch', 'get'])
    def parents(self, request, pk=None):
        """
        Returns a list of all the group names that the given
        user belongs to.
        """
        if(request.method != 'GET'):
            new_parents = [get_object_or_404(models.Object, id=i) for i in request.data]

        obj = self.get_object()
        serializer = self.serializer_class(obj, context=dict(request=request))
        
        if(request.method == 'GET'):
            parents = obj.parents.all()
        else:
            new_parents = serializer.validate_parents(new_parents)
            if request.method in ('POST', 'PUT'):
                models.Relationship.objects.filter(child=obj).delete()
                models.Relationship.objects.bulk_create([
                    models.Relationship(child=obj, parent=p) for p in new_parents
                ])
                parents = new_parents
            elif request.method == 'PATCH':
                models.Relationship.objects.bulk_create([
                    models.Relationship(child=obj, parent=p) for p in new_parents
                ])
                parents = obj.parents.all()
        
        return response.Response([p.id for p in parents])

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
