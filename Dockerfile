FROM python:3
MAINTAINER Phil Christensen <phil@bubblehouse.org>
LABEL Name="antioch"
LABEL Version="0.9"

# Install base dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y sqlite3 ssl-cert

WORKDIR /usr/src/app

# Install Python application dependencies
ADD requirements.txt /usr/src/app/requirements.txt
RUN pip install -r /usr/src/app/requirements.txt

ADD . /usr/src/app
ADD bin/entrypoint.sh /entrypoint.sh

RUN mkdir /var/lib/celery

# Some helpers for temporary Travis conflicts
RUN mkdir -p /home/travis/build/philchristensen
RUN ln -s /usr/src/app /home/travis/build/philchristensen/antioch

# Custom entrypoint for improved ad-hoc command support
ENTRYPOINT ["/entrypoint.sh"]
