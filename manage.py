import os

os.environ['DJANGO_SETTINGS_FILE'] = 'antioch.settings'

from antioch import settings
from django.core.management import execute_manager

if __name__ == "__main__":
	execute_manager(settings)
