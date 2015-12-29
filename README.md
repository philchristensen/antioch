antioch 
=======

(c) Phil Christensen, <phil@bubblehouse.org>

12 January 2014

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

* Flexible plugin system, highly scalable execution layer using Celery and RabbitMQ


antioch is made available under the MIT/X Consortium license.

The included LICENSE file describes this in detail.

Running
--------

The Docker build is currently in development, but it's the only way I'm running in dev
moving forward, so it should stablize quickly.

You'll need a local installation of Docker Compose, perferably via Docker Toolbox.

To install:

    git clone ssh://git@github.com/philchristensen/antioch.git
    cd antioch
    docker-compose up

After first install, and after model or static file changes, you'll need to run migrate
and/or collectstatic:

    docker-compose run web manage.py migrate
    docker-compose run web manage.py collectstatic

Finally, the first time you run, set up a basic database with some sample objects and users:

    docker-compose run web manage.py mkspace

This build uses port 80/443 on your docker machine, but you can use whatever domain name
to refer to it. I have a `docker` alias setup in my `/etc/hosts` file for this purpose.
To find out the address of your docker machine, you can run:

    docker-machine ip default

Connect to the docker machine via your browser, and login with username/passwd `wizard:wizard`.