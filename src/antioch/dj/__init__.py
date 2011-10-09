import crypt

from antioch.dj.core.models import Player

class AntiochAuthBackend:
	"""
	Authenticate against the antioch object database.
	"""
	supports_object_permissions = False
	supports_anonymous_user = True
	supports_inactive_user = False

	def authenticate(self, username=None, password=None, request=None):
		try:
			p = Player.objects.filter(
				avatar__name__iexact = username,
			)[:1]
			
			if not(p):
				print >>sys.stderr, "Django auth failed."
				return None
			
			p = p[0]
			if(p.crypt != crypt.crypt(password, p.crypt[0:2])):
				return None
			return p
		except Player.DoesNotExist:
			print >>sys.stderr, "Player auth failed."
			return None
		except Exception, e:
			import traceback
			e = traceback.format_exc()
			print >>sys.stderr, "Error in authenticate(): %s" % e

	def get_user(self, user_id):
		try:
			p = Player.objects.get(pk=user_id)
			if(p):
				return p
			return None
		except Player.DoesNotExist:
			return None

