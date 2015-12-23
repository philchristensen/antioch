from django.core.management.base import BaseCommand, CommandError

from django.conf import settings

class Command(BaseCommand):
    help = 'Initialize a new database.'

    def add_arguments(self, parser):
        # parser.add_argument('poll_id', nargs='+', type=int)
        parser.add_argument('--with-psql', dest='with-psql')
        parser.add_argument('--schema-file', dest='schema-file')
        parser.add_argument('--bootstrap-file', dest='bootstrap-file')
        parser.add_argument('--no-init', dest='no-init')

    def handle(self, *args, **config):
    	if(config['schema-file']):
    		schema_path = config['schema-file']
    	else:
    		schema_path = pkg.resource_filename('antioch.core.bootstrap', default_schema_path)
    	schema_path = os.path.abspath(schema_path)

    	if(config['bootstrap-file']):
    		bootstrap_path = config['bootstrap-file']
    	else:
    		bootstrap_path = pkg.resource_filename('antioch.core.bootstrap', default_bootstrap_path % config['dataset-name'])
    	bootstrap_path = os.path.abspath(bootstrap_path)
	
    	if not(config['no-init']):
    		bootstrap.initialize_database(config['with-psql'], config['db-url'], config['psql-args'], quiet=False)
	
    	from django.core.management import call_command
    	call_command('syncdb', interactive=False)
    	call_command('migrate', interactive=False)
	
    	pool = dbapi.connect(config['db-url'])
    	bootstrap.load_python(pool, bootstrap_path)
    	bootstrap.initialize_plugins(pool)
        