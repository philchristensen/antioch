from rest_framework import serializers
from django.db import connection

from . import models, exchange

class PermissionValidationMixin(object):
    def get_exchange(self):
        return exchange.ObjectExchange(connection, ctx=self.context['request'].user.avatar.pk)
    
    def check(self, field, permission, value):
        ex = self.get_exchange()
        user = ex.get_object(self.context['request'].user.avatar.id)
        obj = ex.get_object(value.id)
        if not ex.is_allowed(user, permission, obj):
            raise serializers.ValidationError(f"You do not have permission to change the {field}.")
        return value

class ObjectSerializer(serializers.ModelSerializer, PermissionValidationMixin):
    class Meta:
        model = models.Object
        fields = ('id', 'name', 'unique_name', 'owner', 'location',
                'observers', 'parents', 'contents', 'properties', 'verbs')
        read_only_fields = ('observers', 'parents', 'contents', 'properties', 'verbs')
    
    def validate_name(self, value):
        return self.check('name', 'write', value)
    
    def validate_unique_name(self, value):
        return self.check('unique_name', 'write', value)
    
    def validate_owner(self, value):
        return self.check('owner', 'entrust', value)
    
    def validate_location(self, value):
        return self.check('location', 'move', value)
    
    # called by ObjectViewSet
    def validate_parents(self, value):
        self.check('parents', 'transmute', self.instance)
        for parent in value:
            self.check(f'parents to include {parent}', 'derive', parent)
        return value

class VerbSerializer(serializers.ModelSerializer, PermissionValidationMixin):
    class Meta:
        model = models.Verb
        fields = ('id', 'code', 'filename', 'owner', 'origin', 'ability', 'method')
    
    def validate_owner(self, value):
        return self.check('code', 'write', value)
    
    def validate_filename(self, value):
        return self.check('filename', 'develop', value)
    
    def validate_owner(self, value):
        return self.check('owner', 'entrust', value)
    
    def validate_origin(self, value):
        return self.check('owner', 'develop', value)
    
    def validate_method(self, value):
        return self.check('method', 'write', value)
    
    def validate_ability(self, value):
        return self.check('ability', 'write', value)

class PropertySerializer(serializers.ModelSerializer, PermissionValidationMixin):
    class Meta:
        model = models.Property
        fields = ('id', 'name', 'value', 'type', 'owner', 'origin')
    
    def validate_name(self, value):
        return self.check('name', 'write', value)
    
    def validate_value(self, value):
        return self.check('value', 'write', value)
    
    def validate_type(self, value):
        return self.check('type', 'write', value)
    
    def validate_owner(self, value):
        return self.check('owner', 'entrust', value)
    
    def validate_origin(self, value):
        return self.check('owner', 'develop', value)

class AccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Access
        fields = ('id', 'object', 'verb', 'property', 'rule', 'permission', 'type', 'accessor', 'group', 'weight')
