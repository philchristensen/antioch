from django.db import models

class Object(models.Model):
	class Meta:
		db_table = 'object'
		managed = False
	
	name = models.CharField(max_length=255)
	unique_name = models.BooleanField()
	owner = models.ForeignKey('self', related_name='+')
	location = models.ForeignKey('self', related_name='contents', null=True)
	parents = models.ManyToManyField('self', related_name='children', symmetrical=False, through='Relationship')
	observers = models.ManyToManyField('self', related_name='observing', symmetrical=False, through='Observation')
	
	def __unicode__(self):
		return u"#%s (%s)" % (self.id, self.name)

class Relationship(models.Model):
	class Meta:
		db_table = 'object_relation'
		managed = False
	
	child = models.ForeignKey(Object, related_name='parent')
	parent = models.ForeignKey(Object, related_name='child')
	weight = models.IntegerField()

class Observation(models.Model):
	class Meta:
		db_table = 'object_observer'
		managed = False
	
	object = models.ForeignKey(Object, related_name='observer')
	observer = models.ForeignKey(Object, related_name='object')

class Alias(models.Model):
	class Meta:
		verbose_name_plural = 'aliases'
		db_table = 'object_alias'
		managed = False
	
	object = models.ForeignKey(Object, related_name='aliases')
	alias = models.CharField(max_length=255)

class Verb(models.Model):
	class Meta:
		db_table = 'verb'
		managed = False
	
	code = models.TextField()
	filename = models.CharField(max_length=255)
	owner = models.ForeignKey(Object, related_name='verbs')
	origin = models.ForeignKey(Object, related_name='local_verbs')
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
		managed = False
	
	verb = models.ForeignKey(Verb, related_name='names')
	name = models.CharField(max_length=255)
	
	def __unicode__(self):
		return u"%s {#%s on %s}" % (
			self.name, self.verb.id, self.verb.origin
		)


class Property(models.Model):
	class Meta:
		verbose_name_plural = 'properties'
		db_table = 'property'
		managed = False
	
	name = models.CharField(max_length=255)
	value = models.TextField()
	owner = models.ForeignKey(Object, related_name='properties')
	origin = models.ForeignKey(Object, related_name='local_properties')
	
	def __unicode__(self):
		return u'%s {#%s on %s}' % (self.name, self.id, self.origin)

class Permission(models.Model):
	class Meta:
		db_table = 'permission'
		managed = False
	
	name = models.CharField(max_length=255)
	
	def __unicode__(self):
		return self.name

class Access(models.Model):
	class Meta:
		verbose_name_plural = 'access controls'
		db_table = 'access'
		managed = False
	
	object = models.ForeignKey(Object, related_name='acl', null=True)
	verb = models.ForeignKey(Verb, related_name='acl', null=True)
	property = models.ForeignKey(Property, related_name='acl', null=True)
	rule = models.CharField(max_length=5, choices=(('allow', 'allow'), ('deny', 'deny')))
	permission = models.ForeignKey(Permission, related_name='usage')
	type = models.CharField(max_length=8, choices=(('accessor', 'accessor'), ('group', 'group')))
	accessor = models.ForeignKey(Object, related_name='rights')
	group = models.CharField(max_length=8, choices=(('everyone', 'everyone'), ('owners', 'owners'), ('wizards', 'wizards')))
	weight = models.IntegerField()
	
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
		managed = False
	
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
	
	avatar = models.ForeignKey(Object)
	session_id = models.CharField(max_length=255)
	wizard = models.BooleanField()
	crypt = models.CharField(max_length=255)
	last_login = models.DateTimeField()
	last_logout = models.DateTimeField()

class Task(models.Model):
	class Meta:
		db_table = 'task'
		managed = False
	
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
