FROM ubuntu:16.04
MAINTAINER Phil Christensen <phil@bubblehouse.org>
LABEL Name="antioch"
LABEL Version="0.9"

# Install base dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y awscli \
    libffi-dev wget ruby ruby-dev build-essential git python python-dev \
    python-setuptools libpq-dev libldap2-dev libsasl2-dev libxslt-dev \
    sqlite3 ssl-cert nano libpcre3 libpcre3-dev

# Install Python essentials
RUN easy_install pip
RUN pip install -U pip
RUN pip install certifi pyopenssl ndg-httpsclient pyasn1 uwsgi

WORKDIR /opt/django

# Install Python application dependencies
ADD requirements.txt /opt/django/requirements.txt
RUN pip install -r /opt/django/requirements.txt

ADD . /opt/django
ADD bin/entrypoint.sh /entrypoint.sh

RUN mkdir /var/lib/celery

# Custom entrypoint for improved ad-hoc command support
ENTRYPOINT ["/entrypoint.sh"]
