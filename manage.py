import os

os.environ['DJANGO_SETTINGS_FILE'] = 'antioch.dj.settings'

from antioch.dj import settings
from django.core.management import execute_manager

if __name__ == "__main__":
	execute_manager(settings)
