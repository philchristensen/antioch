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

CSRF_TRUSTED_ORIGINS = ['antioch.bubblehouse.org']
ALLOWED_HOSTS = ['antioch.bubblehouse.org', '.execute-api.us-east-2.amazonaws.com']

if os.environ.get('ROLE') in ('celeryflower', 'worker', 'beat'):
    DEBUG = False
    ALLOWED_HOSTS += ['testserver']

STATIC_ROOT = "/tmp/antioch-static"

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
    "LOCATION": "redis://prod-redis.antioch.local:6379/0"
})

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
STATICFILES_STORAGE = "antioch.storage.S3Boto3ManifestStorage"
AWS_STORAGE_BUCKET_NAME = "antioch-prod-staticbucket-kyam05xfedr4"
AWS_DEFAULT_ACL = "public-read"
AWS_QUERYSTRING_AUTH = False