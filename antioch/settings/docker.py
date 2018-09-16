import os

from .base import *

CSRF_TRUSTED_ORIGINS = ['localhost']

if os.environ.get('ROLE') in ('celeryflower', 'worker', 'beat'):
    DEBUG = False
    ALLOWED_HOSTS += ['testserver']

STATIC_ROOT = "/usr/src/app/static"

CELERY_BROKER_URL = os.environ['BROKER_URL']
CELERY_RESULT_BACKEND = os.environ['RESULT_BACKEND']

DATABASES['default'].update({
    "HOST": os.environ['DB_HOST'],
    "PORT": os.environ['DB_PORT'],
    "NAME": os.environ['DB_NAME'],
    "USER": os.environ['DB_USER'],
    "PASSWORD": os.environ['DB_PASSWD']
})

CACHES['default'].update({
    "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
    "LOCATION": os.environ['MEMCACHE']
})
