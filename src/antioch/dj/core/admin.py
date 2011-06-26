from antioch.dj.core import models
from django.contrib import admin

class ObjectAdmin(admin.ModelAdmin):
	list_display = ('__unicode__', 'unique_name', 'owner', 'location')
admin.site.register(models.Object, ObjectAdmin)

admin.site.register(models.Verb)
admin.site.register(models.Property)
admin.site.register(models.Permission)

class AccessAdmin(admin.ModelAdmin):
	list_display = ('rule', 'actor', 'action', 'entity')
	
	def actor(self, obj):
		return obj.actor()
	
	def entity(self, obj):
		return obj.entity()
	
	def action(self, obj):
		return obj.permission.name
admin.site.register(models.Access, AccessAdmin)

admin.site.register(models.Player)
admin.site.register(models.Task)