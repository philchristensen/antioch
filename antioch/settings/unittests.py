import os.path

from .base import *

DATABASES['default'].update({
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": os.path.join(os.environ['HOME'], '.cache/sqlite/antioch.db')
})
