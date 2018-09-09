FROM python:3.7
MAINTAINER Phil Christensen <phil@bubblehouse.org>
LABEL Name="antioch"
LABEL Version="0.9"

# Install base dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y sqlite3 ssl-cert git

ENV PIP_SRC=/usr/src
WORKDIR /usr/src/app

ADD Pipfile /usr/src/app/Pipfile
ADD Pipfile.lock /usr/src/app/Pipfile.lock

# Install Python application dependencies
RUN pip install -q pipenv
RUN pipenv install --system --dev --deploy --ignore-pipfile

ADD . /usr/src/app
ADD bin/entrypoint.sh /entrypoint.sh

RUN mkdir /var/lib/celery

# Some helpers for temporary Travis conflicts
RUN mkdir -p /home/travis/build/philchristensen
RUN ln -s /usr/src/app /home/travis/build/philchristensen/antioch

# Custom entrypoint for improved ad-hoc command support
ENTRYPOINT ["/entrypoint.sh"]
