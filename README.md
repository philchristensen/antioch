antioch 
=======

[![build-status](https://travis-ci.org/philchristensen/antioch.svg?branch=master)](https://travis-ci.org/philchristensen/antioch)
[![python-versions](https://img.shields.io/badge/Python-3.6-brightgreen.svg)](https://www.python.org)
[![django-versions](https://img.shields.io/badge/Django-2.1-blue.svg)](https://www.djangoproject.com)

(c) Phil Christensen, <phil@bubblehouse.org>

4 March 2018

Introduction
-------------

antioch is a next-generation [MUD](http://en.wikipedia.org/wiki/MUD)/[MOO](http://en.wikipedia.org/wiki/MOO)-like
virtual world engine. A scalable architecture lays the foundation for huge, highly customizable virtual worlds, while
sandboxed code execution allows users to author content in a secure and robust environment.

![screenshot](https://github.com/philchristensen/antioch/raw/master/doc/img/screenshot.png "Sample Screenshot")

Feature Set
-----------

* Django-powered, standards-compliant web interface using Bootstrap, jQuery, REST and COMET

* Sandboxed Pure-Python execution enables live programming of in-game code

* PostgreSQL-backed object store scales to million of objects and provides transactional security during verb execution

* Flexible plugin system, highly scalable execution layer using Celery and Redis


antioch is made available under the MIT/X Consortium license.

The included LICENSE file describes this in detail.

Running
--------

You'll need a local installation of Docker Compose, perferably via Docker Toolbox.

To install:

    git clone ssh://git@github.com/philchristensen/antioch.git
    cd antioch
    cp docker-compose.override.yml.example docker-compose.override.yml
    cp antioch/settings/development.py.example antioch/settings/development.py
    docker-compose up

After first install, and after model or static file changes, you'll need to run migrate
and/or collectstatic:

    docker-compose run webapp manage.py migrate
    docker-compose run webapp manage.py collectstatic

Finally, the first time you run, set up a basic database with some sample objects and users:

    docker-compose run webapp manage.py mkspace

This build uses port 80/443 on your docker machine, but you can use whatever domain name
to refer to it. I have a `docker` alias setup in my `/etc/hosts` file for this purpose.
To find out the address of your docker machine, you can run:

    docker-machine ip default

Connect to the docker machine via your browser, and login with username/passwd `wizard:wizard`.