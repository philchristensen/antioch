#!/bin/bash

export PATH="/bin:/usr/bin:/usr/sbin:/usr/local/bin"

cd /usr/src/app

if [ "$1" = '' ]; then
    if [ "$ROLE" = 'worker' ]; then
        exec celery worker --uid nobody --app=antioch --concurrency=8 --loglevel=INFO
    elif [ "$ROLE" = 'beat' ]; then
        exec celery beat --uid nobody --app=antioch --schedule=/var/lib/celery/beat.db --pidfile=/var/lib/celery/beat.pid
    elif [ "$ROLE" = 'webapp' ]; then
        cp /etc/ssl/certs/ssl-cert-snakeoil.pem /usr/src/app/.
        chown www-data:www-data /usr/src/app/ssl-cert-snakeoil.pem
        cp /etc/ssl/private/ssl-cert-snakeoil.key /usr/src/app/.
        chown www-data:www-data /usr/src/app/ssl-cert-snakeoil.key
        exec uwsgi --uid www-data --ini conf/web/uwsgi.ini
    elif [ "$ROLE" = '' ]; then
        echo "Exiting, ROLE not set."
    else
        echo "Exiting, unknown ROLE: $ROLE"
    fi
elif [ "$1" = 'manage.py' ]; then
    exec python3.6 "$@"
elif [ "$1" = 'lint' ]; then
    exec pylint antioch
    ret=$?
    if [[ "$ret" -eq "0" || "$ret" -eq "4" || "$ret" -eq "8" || "$ret" -eq "16" ]]; then
        exit 0
    else
        exit 1
    fi
else
    exec "$@"
fi
