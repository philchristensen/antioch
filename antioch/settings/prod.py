import os

from .base import *

INSTALLED_APPS += ['zappa_django_utils']

CSRF_TRUSTED_ORIGINS = ['localhost']

if os.environ.get('ROLE') in ('celeryflower', 'worker', 'beat'):
    DEBUG = False
    ALLOWED_HOSTS += ['testserver']

STATIC_ROOT = "/usr/src/app/static"

CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

DATABASES['default'].update({
    "HOST": os.environ['DB_HOST'],
    "PORT": os.environ['DB_PORT'],
    "NAME": "antioch",
    "USER": "antioch",
    "PASSWORD": os.environ['DB_PASSWD'],
    'OPTIONS': {
        'sslmode': 'require',
    }
})

CACHES['default'].update({
    "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
    "LOCATION": os.environ['MEMCACHE']
})
