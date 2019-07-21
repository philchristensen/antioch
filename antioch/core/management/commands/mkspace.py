import pkg_resources as pkg

from django.shortcuts import get_object_or_404
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection

from antioch.core.bootstrap import load_python, initialize_plugins
from antioch.core.models import Repository

builtin_templates = ['minimal', 'default']

class Command(BaseCommand):
    help = 'Initialize a new database.'

    def add_arguments(self, parser):
        parser.add_argument('--bootstrap', type=str, default='default',
            help="Optionally pass a built-in template name or a Python source file"
                 " to bootstrap the database.")

    def handle(self, bootstrap='default', *args, **config):
        try:
            repo = Repository.objects.get(slug='default')
            # raise RuntimeError("Looks like mkspace has already been run in this database.")
        except Repository.DoesNotExist:
            repo = Repository(slug='default', url=settings.DEFAULT_GIT_REPO_URL)
            repo.save()

        if(bootstrap in builtin_templates):
            bootstrap_path = pkg.resource_filename('antioch.core.bootstrap', '%s.py' % bootstrap)
        else:
            bootstrap_path = bootstrap
        
        load_python(connection, bootstrap_path)
        initialize_plugins(connection)
