import os

from .base import *

if os.environ.get('CELERY_WORKER'):
    DEBUG = False
else:
    DEBUG = True

STATIC_ROOT = "/opt/django/static"

BROKER_URL = os.environ['BROKER_URL']
CELERY_RESULT_BACKEND = os.environ['RESULT_BACKEND']
CELERY_ALWAYS_EAGER = False

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
