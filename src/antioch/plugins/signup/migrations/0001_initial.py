# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RegisteredPlayer'
        db.create_table('signup_registeredplayer', (
            ('player_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.Player'], unique=True, primary_key=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('activation_key', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('signup', ['RegisteredPlayer'])


    def backwards(self, orm):
        # Deleting model 'RegisteredPlayer'
        db.delete_table('signup_registeredplayer')


    models = {
        'core.object': {
            'Meta': {'object_name': 'Object', 'db_table': "'object'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'contents'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['core.Object']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'observers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'observing'", 'symmetrical': 'False', 'through': "orm['core.Observation']", 'to': "orm['core.Object']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['core.Object']"}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'children'", 'symmetrical': 'False', 'through': "orm['core.Relationship']", 'to': "orm['core.Object']"}),
            'unique_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'core.observation': {
            'Meta': {'object_name': 'Observation', 'db_table': "'object_observer'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'observer'", 'to': "orm['core.Object']"}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'object'", 'to': "orm['core.Object']"})
        },
        'core.player': {
            'Meta': {'object_name': 'Player', 'db_table': "'player'"},
            'avatar': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Object']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'crypt': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'last_logout': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'wizard': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'core.relationship': {
            'Meta': {'object_name': 'Relationship', 'db_table': "'object_relation'"},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'parent'", 'to': "orm['core.Object']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child'", 'to': "orm['core.Object']"}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'signup.registeredplayer': {
            'Meta': {'object_name': 'RegisteredPlayer', '_ormbases': ['core.Player']},
            'activation_key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'player_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.Player']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['signup']