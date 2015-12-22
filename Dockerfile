FROM ubuntu:14.04.2
MAINTAINER Phil Christensen <pchristensen@logicworks.net>

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y awscli libffi-dev wget ruby2.0 ruby-dev build-essential git python python-dev python-setuptools libpq-dev libldap2-dev libsasl2-dev libxslt-dev nginx sqlite3 supervisor ssl-cert nano

RUN easy_install pip
RUN pip install -U pip
RUN pip install certifi pyopenssl ndg-httpsclient pyasn1
RUN pip install uwsgi

ADD requirements.txt /opt/django/requirements.txt
RUN pip install -r /opt/django/requirements.txt

RUN gem install redmon

RUN useradd --system supervisor
RUN useradd --system uwsgi
RUN useradd --system celery
RUN useradd --system redmon

RUN mkdir -p /var/log/supervisor && chown supervisor:supervisor /var/log/supervisor
RUN mkdir -p /var/run/supervisord && chown supervisor:supervisor /var/run/supervisord
RUN mkdir -p /var/lib/uwsgi && chown uwsgi:uwsgi /var/lib/uwsgi 
RUN mkdir -p /var/log/celery && chown celery:celery /var/log/celery
RUN mkdir -p /var/lib/celery && chown celery:celery /var/lib/celery
RUN mkdir -p /var/log/redmon && chown redmon:redmon /var/log/redmon

RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN rm /etc/nginx/sites-enabled/default

VOLUME ["/opt/django"]
EXPOSE 8080
EXPOSE 8443

ADD conf /opt/django/conf
ADD bin/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["supervisord"]
