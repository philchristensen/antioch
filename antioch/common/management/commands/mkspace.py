import pkg_resources as pkg

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection

from antioch.core import bootstrap

builtin_templates = ['minimal', 'default']

class Command(BaseCommand):
    help = 'Initialize a new database.'

    def add_arguments(self, parser):
        parser.add_argument('--bootstrap', type=str, default='default',
            help="Optionally pass a built-in template name or a Python source file"
                 " to bootstrap the database.")

    def handle(self, template='default', *args, **config):
        if(template in builtin_templates):
            bootstrap_path = pkg.resource_filename('antioch.core.bootstrap', '%s.py' % template)
        else:
            bootstrap_path = template
        bootstrap.load_python(connection, bootstrap_path)
        bootstrap.initialize_plugins(connection)
        