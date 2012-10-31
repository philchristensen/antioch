# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

	def forwards(self, orm):
		# Adding model 'Object'
		db.create_table('object', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
			('unique_name', self.gf('django.db.models.fields.BooleanField')(default=False)),
			('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, on_delete=models.SET_NULL, to=orm['core.Object'])),
			('location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='contents', null=True, on_delete=models.SET_NULL, to=orm['core.Object'])),
		))
		db.send_create_signal('core', ['Object'])

		# Adding model 'Relationship'
		db.create_table('object_relation', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('child', self.gf('django.db.models.fields.related.ForeignKey')(related_name='parent', to=orm['core.Object'])),
			('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='child', to=orm['core.Object'])),
			('weight', self.gf('django.db.models.fields.IntegerField')(default=0)),
		))
		db.send_create_signal('core', ['Relationship'])

		# Adding model 'Observation'
		db.create_table('object_observer', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('object', self.gf('django.db.models.fields.related.ForeignKey')(related_name='observer', to=orm['core.Object'])),
			('observer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='object', to=orm['core.Object'])),
		))
		db.send_create_signal('core', ['Observation'])

		# Adding model 'Alias'
		db.create_table('object_alias', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('object', self.gf('django.db.models.fields.related.ForeignKey')(related_name='aliases', to=orm['core.Object'])),
			('alias', self.gf('django.db.models.fields.CharField')(max_length=255)),
		))
		db.send_create_signal('core', ['Alias'])

		# Adding model 'Verb'
		db.create_table('verb', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('code', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
			('filename', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
			('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, on_delete=models.SET_NULL, to=orm['core.Object'])),
			('origin', self.gf('django.db.models.fields.related.ForeignKey')(related_name='verbs', to=orm['core.Object'])),
			('ability', self.gf('django.db.models.fields.BooleanField')(default=False)),
			('method', self.gf('django.db.models.fields.BooleanField')(default=False)),
		))
		db.send_create_signal('core', ['Verb'])

		# Adding model 'VerbName'
		db.create_table('verb_name', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('verb', self.gf('django.db.models.fields.related.ForeignKey')(related_name='names', to=orm['core.Verb'])),
			('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
		))
		db.send_create_signal('core', ['VerbName'])

		# Adding model 'Property'
		db.create_table('property', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
			('value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
			('type', self.gf('django.db.models.fields.CharField')(max_length=255)),
			('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, on_delete=models.SET_NULL, to=orm['core.Object'])),
			('origin', self.gf('django.db.models.fields.related.ForeignKey')(related_name='properties', to=orm['core.Object'])),
		))
		db.send_create_signal('core', ['Property'])

		# Adding model 'Permission'
		db.create_table('permission', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
		))
		db.send_create_signal('core', ['Permission'])

		# Adding model 'Access'
		db.create_table('access', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('object', self.gf('django.db.models.fields.related.ForeignKey')(related_name='acl', null=True, to=orm['core.Object'])),
			('verb', self.gf('django.db.models.fields.related.ForeignKey')(related_name='acl', null=True, to=orm['core.Verb'])),
			('property', self.gf('django.db.models.fields.related.ForeignKey')(related_name='acl', null=True, to=orm['core.Property'])),
			('rule', self.gf('django.db.models.fields.CharField')(max_length=5)),
			('permission', self.gf('django.db.models.fields.related.ForeignKey')(related_name='usage', to=orm['core.Permission'])),
			('type', self.gf('django.db.models.fields.CharField')(max_length=8)),
			('accessor', self.gf('django.db.models.fields.related.ForeignKey')(related_name='rights', null=True, to=orm['core.Object'])),
			('group', self.gf('django.db.models.fields.CharField')(max_length=8, null=True)),
			('weight', self.gf('django.db.models.fields.IntegerField')(default=0)),
		))
		db.send_create_signal('core', ['Access'])

		# Adding model 'Player'
		db.create_table('player', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('avatar', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Object'], null=True, on_delete=models.SET_NULL)),
			('session_id', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
			('wizard', self.gf('django.db.models.fields.BooleanField')(default=False)),
			('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
			('crypt', self.gf('django.db.models.fields.CharField')(max_length=255)),
			('last_login', self.gf('django.db.models.fields.DateTimeField')(null=True)),
			('last_logout', self.gf('django.db.models.fields.DateTimeField')(null=True)),
		))
		db.send_create_signal('core', ['Player'])

		# Adding model 'Task'
		db.create_table('task', (
			('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
			('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tasks', to=orm['core.Object'])),
			('origin', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['core.Object'])),
			('verb_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
			('args', self.gf('django.db.models.fields.TextField')()),
			('kwargs', self.gf('django.db.models.fields.TextField')()),
			('created', self.gf('django.db.models.fields.DateTimeField')()),
			('delay', self.gf('django.db.models.fields.IntegerField')()),
			('killed', self.gf('django.db.models.fields.BooleanField')(default=False)),
			('error', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
			('trace', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
		))
		db.send_create_signal('core', ['Task'])


	def backwards(self, orm):
		# Deleting model 'Object'
		db.delete_table('object')

		# Deleting model 'Relationship'
		db.delete_table('object_relation')

		# Deleting model 'Observation'
		db.delete_table('object_observer')

		# Deleting model 'Alias'
		db.delete_table('object_alias')

		# Deleting model 'Verb'
		db.delete_table('verb')

		# Deleting model 'VerbName'
		db.delete_table('verb_name')

		# Deleting model 'Property'
		db.delete_table('property')

		# Deleting model 'Permission'
		db.delete_table('permission')

		# Deleting model 'Access'
		db.delete_table('access')

		# Deleting model 'Player'
		db.delete_table('player')

		# Deleting model 'Task'
		db.delete_table('task')


	models = {
		'core.access': {
			'Meta': {'object_name': 'Access', 'db_table': "'access'"},
			'accessor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rights'", 'null': 'True', 'to': "orm['core.Object']"}),
			'group': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'acl'", 'null': 'True', 'to': "orm['core.Object']"}),
			'permission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'usage'", 'to': "orm['core.Permission']"}),
			'property': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'acl'", 'null': 'True', 'to': "orm['core.Property']"}),
			'rule': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
			'verb': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'acl'", 'null': 'True', 'to': "orm['core.Verb']"}),
			'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
		},
		'core.alias': {
			'Meta': {'object_name': 'Alias', 'db_table': "'object_alias'"},
			'alias': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'object': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'aliases'", 'to': "orm['core.Object']"})
		},
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
		'core.permission': {
			'Meta': {'object_name': 'Permission', 'db_table': "'permission'"},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
		'core.property': {
			'Meta': {'object_name': 'Property', 'db_table': "'property'"},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
			'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'properties'", 'to': "orm['core.Object']"}),
			'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['core.Object']"}),
			'type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
			'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
		},
		'core.relationship': {
			'Meta': {'object_name': 'Relationship', 'db_table': "'object_relation'"},
			'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'parent'", 'to': "orm['core.Object']"}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'child'", 'to': "orm['core.Object']"}),
			'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
		},
		'core.task': {
			'Meta': {'object_name': 'Task', 'db_table': "'task'"},
			'args': ('django.db.models.fields.TextField', [], {}),
			'created': ('django.db.models.fields.DateTimeField', [], {}),
			'delay': ('django.db.models.fields.IntegerField', [], {}),
			'error': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'killed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
			'kwargs': ('django.db.models.fields.TextField', [], {}),
			'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['core.Object']"}),
			'trace': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
			'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': "orm['core.Object']"}),
			'verb_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
		},
		'core.verb': {
			'Meta': {'object_name': 'Verb', 'db_table': "'verb'"},
			'ability': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
			'code': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
			'filename': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'method': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
			'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'verbs'", 'to': "orm['core.Object']"}),
			'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['core.Object']"})
		},
		'core.verbname': {
			'Meta': {'object_name': 'VerbName', 'db_table': "'verb_name'"},
			'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
			'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
			'verb': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['core.Verb']"})
		}
	}

	complete_apps = ['core']