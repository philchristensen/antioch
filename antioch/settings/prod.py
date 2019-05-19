import os

import boto3

from .base import *

ssm = boto3.client('ssm')
response = ssm.get_parameters_by_path(
    Path='/antioch/prod',
    WithDecryption=True
)
SSM_PARAMS = {x['Name'].split('/')[-1]:x['Value'] for x in response['Parameters']}

INSTALLED_APPS += ['zappa_django_utils']

CSRF_TRUSTED_ORIGINS = ['localhost']

if os.environ.get('ROLE') in ('celeryflower', 'worker', 'beat'):
    DEBUG = False
    ALLOWED_HOSTS += ['testserver']

STATIC_ROOT = "/usr/src/app/static"

CELERY_BROKER_URL = 'redis://prod-redis.antioch.local:6379/0'
CELERY_RESULT_BACKEND = 'redis://prod-redis.antioch.local:6379/0'

DATABASES['default'].update({
    "HOST": os.environ['DB_HOST'],
    "PORT": os.environ['DB_PORT'],
    "NAME": "antioch",
    "USER": "antioch",
    "PASSWORD": SSM_PARAMS['db-password'],
    'OPTIONS': {
        'sslmode': 'require',
    }
})

CACHES['default'].update({
    "BACKEND": "redis_cache.RedisCache",
    "LOCATION": "rediss://prod-redis.antioch.local:6379/0"
})
