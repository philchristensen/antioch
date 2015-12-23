import pkg_resources as pkg

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from antioch.core import dbapi, bootstrap

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
        pool = dbapi.connect(settings.DB_URL)
        bootstrap.load_python(pool, bootstrap_path)
        bootstrap.initialize_plugins(pool)
        