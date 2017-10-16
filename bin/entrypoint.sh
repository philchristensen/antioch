#!/bin/bash -x

export PATH="/bin:/usr/bin:/usr/sbin:/usr/local/bin"

cd /opt/django

if [ "$1" = '' ]; then
    if [ "$ROLE" = 'worker' ]; then
        exec celery worker --app=antioch --concurrency=8 --loglevel=INFO
    elif [ "$ROLE" = 'beat' ]; then
        exec celery beat --app=antioch --schedule=/var/lib/celery/beat.db
    elif [ "$ROLE" = 'webapp' ]; then
        exec uwsgi --ini conf/web/uwsgi.ini
    elif [ "$ROLE" = 'celeryflower' ]; then
        exec celery flower --app=antioch.celery
    elif [ "$ROLE" = 'redmon' ]; then
        exec redmon --redis "$REDIS_URL"
    elif [ "$ROLE" = '' ]; then
        echo "Exiting, ROLE not set."
    else
        echo "Exiting, unknown ROLE: $ROLE"
    fi
elif [ "$1" = 'manage.py' ]; then
    exec python "$@"
elif [ "$1" = 'lint' ]; then
    pylint antioch
    ret=$?
    if [[ "$ret" -eq "0" || "$ret" -eq "4" || "$ret" -eq "8" || "$ret" -eq "16" ]]; then
        exit 0
    else
        exit 1
    fi
else
    exec "$@"
fi
