from antioch.dj.core import models
from django.contrib import admin

class VerbInline(admin.TabularInline):
	model = models.Verb
	fk_name = 'origin'
	extra = 1
	exclude = ('code',)
	readonly_fields = ('filename', 'owner', 'ability', 'method')

class PropertyInline(admin.TabularInline):
	model = models.Property
	fk_name = 'origin'
	extra = 1
	readonly_fields = ('name', 'value', 'owner')

class ObjectAdmin(admin.ModelAdmin):
	list_display = ('__unicode__', 'unique_name', 'owner', 'location')
	inlines = [
		VerbInline,
		PropertyInline,
	]
admin.site.register(models.Object, ObjectAdmin)

admin.site.register(models.Verb)
admin.site.register(models.Property)
admin.site.register(models.Permission)

class AccessAdmin(admin.ModelAdmin):
	list_display = ('rule', 'actor', 'action', 'entity', 'origin')
	
	def actor(self, obj):
		return obj.actor()
	
	def entity(self, obj):
		return obj.entity()
	
	def origin(self, obj):
		return obj.origin()
	
	def action(self, obj):
		return obj.permission.name
admin.site.register(models.Access, AccessAdmin)

admin.site.register(models.Player)
admin.site.register(models.Task)