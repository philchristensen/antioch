from rest_framework import serializers
from django.db import connection

from . import models, exchange

class PermissionValidationMixin(object):
    def get_exchange(self):
        return exchange.ObjectExchange(connection, ctx=self.context['request'].user.avatar.pk)
    
    def check(self, field, permission, value):
        import pdb; pdb.set_trace()
        ex = self.get_exchange()
        user = ex.get_object(self.context['request'].user.avatar.id)
        obj = ex.get_object(value.id)
        if not ex.is_allowed(user, permission, obj):
            raise serializers.ValidationError(f"You do not have permission to change the {field}.")
        return value

class RelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Relationship
        fields = ('id', 'child', 'parent', 'weight')

class ObjectSerializer(serializers.ModelSerializer, PermissionValidationMixin):
    parents = RelationshipSerializer(many=True)
    
    class Meta:
        model = models.Object
        fields = ('id', 'name', 'unique_name', 'owner', 'location', 'parents')
        read_only_fields = ('observers',)
    
    def validate_owner(self, value):
        return self.check('owner', 'entrust', value)
    
    def validate_location(self, value):
        return self.check('location', 'move', value)

class VerbSerializer(serializers.ModelSerializer, PermissionValidationMixin):
    class Meta:
        model = models.Verb
        fields = ('id', 'code', 'filename', 'owner', 'origin', 'ability', 'method')
    
    def validate_owner(self, value):
        return self.check('owner', 'entrust', value)

class PropertySerializer(serializers.ModelSerializer, PermissionValidationMixin):
    class Meta:
        model = models.Property
        fields = ('id', 'name', 'value', 'type', 'owner', 'origin')
    
    def validate_owner(self, value):
        return self.check('owner', 'entrust', value)

class AccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Access
        fields = ('id', 'object', 'verb', 'property', 'rule', 'permission', 'type', 'accessor', 'group', 'weight')
