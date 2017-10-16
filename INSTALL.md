antioch Installation
====================

by Phil Christensen
phil@bubblehouse.org

Requirements for Server
-----------------------

* [Redis             >=  3.0.6 ](http://www.redis.io)
* [PostgreSQL        >=  9.3   ](http://www.postgresql.org)
* [Python            >=  2.7   ](http://www.python.org)
* [Django            >=  1.9   ](http://www.djangoproject.com)
* [Celery            >=  3.1.19](http://www.celeryproject.com)
* [Twisted           >= 15.5   ](http://www.twistedmatrix.com)
* [RestrictedPython  >=  3.6.0 ](http://pypi.python.org/pypi/RestrictedPython)

There are various other requirements

Requirements for Client
-----------------------

Pretty much any WebKit- or Mozilla-based browser should work. Opera
and Internet Exporer 6 or better should also work, but neither is
supported at this time.

* [Firefox](http://www.mozilla.com/firefox)
* [Safari](http://www.apple.com/safari)
* [Chrome](http://google.com/chrome)

Running the Server
-------------------
You'll need a local installation of Docker Compose, perferably via Docker Toolbox.

To install:

    git clone ssh://git@github.com/philchristensen/antioch.git
    cd antioch
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

Running the Client
------------------

Connect to: <https://docker>

Login with username and password: `wizard/wizard`

Obviously, once in, it's a pretty good idea to change your password for the 
wizard account, which you can do with the `passwd` command.

If you'd like a more specific name for your administrator character, for the 
moment you can use:

    exec caller.set_name("My Name", real=True)

Setting the `gravatar_id` property will load a user icon for you from the 
Gravatar.com web service.

    set gravatar_id on wizard to user@example.com
