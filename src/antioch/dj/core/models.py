from django.db import models

class Object(models.Model):
	class Meta:
		db_table = 'object'
	
	name = models.CharField(max_length=255)
	unique_name = models.BooleanField()
	owner = models.ForeignKey('self', related_name='+')
	location = models.ForeignKey('self', related_name='contents')
	parents = models.ManyToManyField('self', related_name='children', symmetrical=False, through='Relationship')
	observers = models.ManyToManyField('self', related_name='observing', symmetrical=False, through='Observation')

class Relationship(models.Model):
	class Meta:
		db_table = 'object_relation'
	
	child = models.ForeignKey(Object, related_name='parent')
	parent = models.ForeignKey(Object, related_name='child')
	weight = models.IntegerField()

class Observation(models.Model):
	class Meta:
		db_table = 'object_observer'
	
	object = models.ForeignKey(Object, related_name='observer')
	observer = models.ForeignKey(Object, related_name='object')

class Alias(models.Model):
	class Meta:
		db_table = 'object_alias'
	
	object = models.ForeignKey(Object, related_name='aliases')
	alias = models.CharField(max_length=255)

class Verb(models.Model):
	class Meta:
		db_table = 'verb'
	
	code = models.TextField()
	filename = models.CharField(max_length=255)
	owner = models.ForeignKey(Object, related_name='verbs')
	origin = models.ForeignKey(Object, related_name='local_verbs')
	ability = models.BooleanField()
	method = models.BooleanField()

class VerbName(models.Model):
	class Meta:
		db_table = 'verb_name'
	
	verb = models.ForeignKey(Verb, related_name='names')
	name = models.CharField(max_length=255)

class Property(models.Model):
	class Meta:
		db_table = 'property'
	
	name = models.CharField(max_length=255)
	value = models.TextField()
	owner = models.ForeignKey(Object, related_name='properties')
	origin = models.ForeignKey(Object, related_name='local_properties')

class Permission(models.Model):
	class Meta:
		db_table = 'permission'
	
	name = models.CharField(max_length=255)

class Access(models.Model):
	class Meta:
		db_table = 'access'
	
	object = models.ForeignKey(Object, related_name='acl')
	verb = models.ForeignKey(Verb, related_name='acl')
	property = models.ForeignKey(Property, related_name='acl')
	rule = models.CharField(max_length=5, choices=(('allow', 'allow'), ('deny', 'deny')))
	permission = models.ForeignKey(Permission, related_name='usage')
	type = models.CharField(max_length=8, choices=(('accessor', 'accessor'), ('group', 'group')))
	accessor = models.ForeignKey(Object, related_name='rights')
	group = models.CharField(max_length=8, choices=(('everyone', 'everyone'), ('owners', 'owners'), ('wizards', 'wizards')))
	weight = models.IntegerField()

class Player(models.Model):
	class Meta:
		db_table = 'player'
	
	avatar = models.ForeignKey(Object)
	session_id = models.CharField(max_length=255)
	wizard = models.BooleanField()
	crypt = models.CharField(max_length=255)
	last_login = models.DateTimeField()
	last_logout = models.DateTimeField()

class Task(models.Model):
	class Meta:
		db_table = 'task'
	
	user = models.ForeignKey(Object, related_name='tasks')
	origin = models.ForeignKey(Object, related_name='+')
	verb_name = models.CharField(max_length=255)
	args = models.TextField()
	kwargs = models.TextField()
	created = models.DateTimeField()
	delay = models.IntegerField()
	killed = models.BooleanField()
	error = models.CharField(max_length=255)
	trace = models.TextField()
