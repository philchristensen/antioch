from django.shortcuts import get_object_or_404
from django.db import connection

from rest_framework import viewsets, response, exceptions
from rest_framework.decorators import action

from . import models, serializers, exchange

class MultiEntityMixin(object):
    def get_queryset_for_model(self, klass):
        if(self.request.GET):
            ex = exchange.ObjectExchange(connection, ctx=self.request.user.avatar.pk)
            queryset = klass.objects.filter(id__in=self.request.GET.getlist('id'))
            for obj in queryset:
                user = ex.get_object(self.request.user.avatar.pk)
                obj = ex.load(self.basename, obj.pk)
                ex.is_allowed(user, 'read', obj)
            return queryset
        elif('pk' in self.request.parser_context['kwargs']):
            return klass.objects.filter(pk=self.request.parser_context['kwargs']['pk'])
        elif(self.basename == 'object'):
            return klass.objects.filter(location=self.request.user.avatar.location)
        else:
            return self.queryset

class ObjectViewSet(viewsets.ModelViewSet, MultiEntityMixin):
    """
    API endpoint that allows objects to be viewed or edited.
    """
    queryset = models.Object.objects.none()
    serializer_class = serializers.ObjectSerializer

    def get_queryset(self):
        return self.get_queryset_for_model(models.Object)

    @action(detail=True, methods=['post', 'put', 'patch', 'get'])
    def parents(self, request, pk=None):
        """
        An API endpoint for editing object parents.
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

class VerbViewSet(viewsets.ModelViewSet, MultiEntityMixin):
    """
    API endpoint that allows verbs to be viewed or edited.
    """
    queryset = models.Verb.objects.none()
    serializer_class = serializers.VerbSerializer
    
    def get_queryset(self):
        return self.get_queryset_for_model(models.Verb)

class PropertyViewSet(viewsets.ModelViewSet, MultiEntityMixin):
    """
    API endpoint that allows properties to be viewed or edited.
    """
    queryset = models.Property.objects.none()
    serializer_class = serializers.PropertySerializer
    
    def get_queryset(self):
        return self.get_queryset_for_model(models.Property)

class AccessViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows access rules to be viewed or edited.
    """
    queryset = models.Access.objects.all()
    serializer_class = serializers.AccessSerializer
