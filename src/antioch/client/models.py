# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

from django.db import models

class Object(models.Model):
	class Meta:
		db_table = 'object'
	
	name = models.CharField(max_length=255)
	unique_name = models.BooleanField()
	owner = models.ForeignKey('self', related_name='+', null=True, on_delete=models.SET_NULL)
	location = models.ForeignKey('self', related_name='contents', null=True, on_delete=models.SET_NULL)
	parents = models.ManyToManyField('self', related_name='children', symmetrical=False, through='Relationship')
	observers = models.ManyToManyField('self', related_name='observing', symmetrical=False, through='Observation')
	
	def __unicode__(self):
		return u"#%s (%s)" % (self.id, self.name)

class Relationship(models.Model):
	class Meta:
		db_table = 'object_relation'
	
	child = models.ForeignKey(Object, related_name='parent', on_delete=models.CASCADE)
	parent = models.ForeignKey(Object, related_name='child', on_delete=models.CASCADE)
	weight = models.IntegerField(default=0)

class Observation(models.Model):
	class Meta:
		db_table = 'object_observer'
	
	object = models.ForeignKey(Object, related_name='observer', on_delete=models.CASCADE)
	observer = models.ForeignKey(Object, related_name='object', on_delete=models.CASCADE)

class Alias(models.Model):
	class Meta:
		verbose_name_plural = 'aliases'
		db_table = 'object_alias'
	
	object = models.ForeignKey(Object, related_name='aliases', on_delete=models.CASCADE)
	alias = models.CharField(max_length=255)

class Verb(models.Model):
	class Meta:
		db_table = 'verb'
	
	code = models.TextField()
	filename = models.CharField(max_length=255, blank=True, null=True)
	owner = models.ForeignKey(Object, related_name='+', null=True, on_delete=models.SET_NULL)
	origin = models.ForeignKey(Object, related_name='verbs', on_delete=models.CASCADE)
	ability = models.BooleanField()
	method = models.BooleanField()
	
	def __unicode__(self):
		return u"%s {#%s on %s}" % (
			self.annotated(), self.id, self.origin
		)
	
	def annotated(self):
		ability_decoration = ['', '@'][self.ability]
		method_decoration = ['', '()'][self.method]
		verb_name = self.name()
		return u''.join([ability_decoration, verb_name, method_decoration])
	
	def name(self):
		return self.names.all()[0].name

class VerbName(models.Model):
	class Meta:
		db_table = 'verb_name'
	
	verb = models.ForeignKey(Verb, related_name='names', on_delete=models.CASCADE)
	name = models.CharField(max_length=255)
	
	def __unicode__(self):
		return u"%s {#%s on %s}" % (
			self.name, self.verb.id, self.verb.origin
		)


class Property(models.Model):
	class Meta:
		verbose_name_plural = 'properties'
		db_table = 'property'
	
	name = models.CharField(max_length=255)
	value = models.TextField()
	type = models.CharField(max_length=255, choices=[(x,x) for x in ('string', 'python', 'dynamic')])
	owner = models.ForeignKey(Object, related_name='+', null=True, on_delete=models.SET_NULL)
	origin = models.ForeignKey(Object, related_name='properties', on_delete=models.CASCADE)
	
	def __unicode__(self):
		return u'%s {#%s on %s}' % (self.name, self.id, self.origin)

class Permission(models.Model):
	class Meta:
		db_table = 'permission'
	
	name = models.CharField(max_length=255)
	
	def __unicode__(self):
		return self.name

class Access(models.Model):
	class Meta:
		verbose_name_plural = 'access controls'
		db_table = 'access'
	
	object = models.ForeignKey(Object, related_name='acl', null=True, on_delete=models.CASCADE)
	verb = models.ForeignKey(Verb, related_name='acl', null=True, on_delete=models.CASCADE)
	property = models.ForeignKey(Property, related_name='acl', null=True, on_delete=models.CASCADE)
	rule = models.CharField(max_length=5, choices=[(x,x) for x in ('allow', 'deny')])
	permission = models.ForeignKey(Permission, related_name='usage', on_delete=models.CASCADE)
	type = models.CharField(max_length=8, choices=[(x,x) for x in ('accessor', 'group')])
	accessor = models.ForeignKey(Object, related_name='rights', null=True, on_delete=models.CASCADE)
	group = models.CharField(max_length=8, null=True, choices=[(x,x) for x in ('everyone', 'owners', 'wizards')])
	weight = models.IntegerField(default=0)
	
	def actor(self):
		return self.accessor if self.type == 'accessor' else self.group
	
	def entity(self):
		if self.object:
			return 'self'
		elif self.verb:
			return ''.join([
				['', '@'][self.verb.ability],
				self.verb.names.all()[:1][0].name,
				['', '()'][self.verb.method],
			])
		else:
			return self.property.name

	def origin(self):
		if self.object:
			return self.object 
		elif self.verb:
			return self.verb.origin
		else:
			return self.property.origin
	
	def __unicode__(self):
		try:
			return '%(rule)s %(actor)s %(permission)s on %(entity)s (%(weight)s)' % dict(
				rule		= self.rule,
				actor		= self.actor(),
				permission	= self.permission.name,
				entity		= self.entity(),
				weight		= self.weight,
			)
		except Exception, e:
			import traceback
			traceback.print_exc();
			return str(e)

class Player(models.Model):
	class Meta:
		db_table = 'player'
	
	def __unicode__(self):
		return self.email

	def is_authenticated(self):
		return True
	
	@property
	def is_active(self):
		return True
	
	@property
	def is_staff(self):
		return False
	
	@property
	def is_superuser(self):
		return False
	
	avatar = models.ForeignKey(Object, null=True, on_delete=models.SET_NULL)
	session_id = models.CharField(max_length=255, null=True)
	wizard = models.BooleanField()
	crypt = models.CharField(max_length=255)
	last_login = models.DateTimeField(null=True)
	last_logout = models.DateTimeField(null=True)

class Task(models.Model):
	class Meta:
		db_table = 'task'
	
	user = models.ForeignKey(Object, related_name='tasks', on_delete=models.CASCADE)
	origin = models.ForeignKey(Object, related_name='+', on_delete=models.CASCADE)
	verb_name = models.CharField(max_length=255)
	args = models.TextField()
	kwargs = models.TextField()
	created = models.DateTimeField()
	delay = models.IntegerField()
	killed = models.BooleanField(default=False)
	error = models.CharField(max_length=255, blank=True, null=True)
	trace = models.TextField(blank=True, null=True)
