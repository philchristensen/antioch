antioch Installation
====================

by Phil Christensen
phil@bubblehouse.org

Requirements for Server
-----------------------

As long as you're using Python 2.6 or better, most recent versions of
everything else should work, but to be specific:

* [RabbitMQ          >=  2.7.1](http://www.rabbitmq.com)
* [PostgreSQL        >=  9.1  ](http://www.postgresql.org)
* [Python            >=  2.7  ](http://www.python.org)
* [Django            >=  1.6.1](http://www.djangoproject.com)
* [South             >=  0.8.4](http://south.aeracode.org)
* [Celery            >=  3.1.7](http://www.celeryproject.com)
* [Twisted           >= 13.2  ](http://www.twistedmatrix.com)
* [RestrictedPython  >=  3.6.0](http://pypi.python.org/pypi/RestrictedPython)

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
Check out the latest version of the code, and cd into the installation directory:

    cd antioch/

Install the required dependencies:

    pip install -r requirements.txt

Install the base system:

    pip install --editbale .

Next you'll need to create the default database:

    mkspace

> By default, `mkspace` tries to connect to a PostgreSQL database running on
> localhost:5432 as the `postgres` super-user.

This should have created the `antioch` user and a corresponding database. It
also ran the Django manage.py commands 'syncdb' and 'migrate'.

Next you should be able to start up the web server with:

    ./manage.py runserver

While in another terminal, you should start up a Celery worker with:

    celery -A antioch worker --loglevel=info

> The default configuration looks for a PostgreSQL server on localhost:5432 and
> a RabbitMQ server on localhost:5672.

Running the Client
------------------

Connect to: <http://localhost:8000>

Login with username and password: `wizard/wizard`

Obviously, once in, it's a pretty good idea to change your password for the 
wizard account, which you can do with the `passwd` command.

If you'd like a more specific name for your administrator character, for the 
moment you can use:

    exec caller.set_name("My Name", real=True)

Setting the `gravatar_id` property will load a user icon for you from the 
Gravatar.com web service.

    set gravatar_id on wizard to user@example.com
