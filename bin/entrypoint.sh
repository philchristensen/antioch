#!/bin/bash
set -e

if [ "$1" = 'supervisord' ]; then
    if [ "$ROLE" = 'web' ]; then
        cp /opt/django/conf/web/celeryflower-restart.crontab /etc/cron.d/celeryflower-restart
        cp /opt/django/conf/web/nginx-uwsgi.conf /etc/nginx/sites-enabled/antioch-web.conf
    fi

    if [ "$ROLE" != '' ]; then
        cp /opt/django/conf/$ROLE/supervisord.conf /etc/supervisor/supervisord.conf
    fi

    exec "/usr/bin/$@" "-c" "/etc/supervisor/supervisord.conf" 
elif [ "$1" = 'manage.py' ]; then
    exec "/usr/bin/python" "/opt/django/$@"
fi

exec "$@"