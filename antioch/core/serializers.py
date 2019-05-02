from rest_framework import serializers

from . import models

class ObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Object
        fields = ('name', 'unique_name', 'owner', 'location', 'parents', 'observers')

class RelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Relationship
        fields = ('child', 'parent', 'weight')

class ObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Observation
        fields = ('object', 'observer')

class AliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Alias
        fields = ('object', 'alias',)

class VerbSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Verb
        fields = ('code', 'filename', 'owner', 'origin', 'ability', 'method')

class VerbNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VerbName
        fields = ('verb', 'name')

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Property
        fields = ('name', 'value', 'type', 'owner', 'origin')

class AccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Access
        fields = ('object', 'verb', 'property', 'rule', 'permission', 'type', 'accessor', 'group', 'weight')

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Player
        fields = ('avatar', 'session_id', 'wizard', 'enabled', 'crypt', 'last_login', 'last_logout')

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Task
        fields = ('user', 'origin', 'verb_name', 'args', 'kwargs', 'created', 'delay', 'killed', 'error', 'trace')
