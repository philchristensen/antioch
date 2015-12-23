from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from antioch.core import dbapi

class Command(BaseCommand):
    help = 'Initialize a new database.'

    def add_arguments(self, parser):
        parser.add_argument('--bootstrap-module', type=str, default='default')

    def handle(self, bootstrap_module=None, *args, **config):
        if(bootstrap_module is None):
            bootstrap_module = 'antioch.core.bootstrap.default'
        pool = dbapi.connect(settings.DB_URL)
        bootstrap.load_python(pool, bootstrap_path)
        bootstrap.initialize_plugins(pool)
        