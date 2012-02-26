antioch Installation
====================

by Phil Christensen
phil@bubblehouse.org

Requirements for Server
-----------------------

As long as you're using Python 2.6 or better, most recent versions of
everything else should work, but to be specific:

* [Python            >=  2.6  ](http://www.python.org)
* [PostgreSQL        >=  9.0  ](http://www.postgresql.org)
* [psycopg2          >=  2.4.1](http://initd.org/psycopg)
* [RabbitMQ          >=  2.7.1](http://www.rabbitmq.com)
* [Pika              >=  0.9.6](https://launchpad.net/txamqp)
* [Django            >=  1.3  ](http://www.djangoproject.com)
* [Twisted           >= 11.0  ](http://www.twistedmatrix.com)
* [ampoule           >=  0.1  ](https://launchpad.net/ampoule)
* [RestrictedPython  >=  3.6.0](http://pypi.python.org/pypi/RestrictedPython)
* [simplejson        >=  2.3.2](http://pypi.python.org/pypi/simplejson)


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

Once you install Python and Twisted, the rest will be taken care of by
the setuptools-based installer.

    python setup.py install

Next you'll need to create the default database:

    mkspace

> By default, `mkspace` tries to connect to a PostgreSQL database running on
> localhost:5432 as the `postgres` super-user.

This should have created the `antioch` user and a corresponding database. For
the time, you'll also have to run the Django syncdb script:

    ./manage.py syncdb --noinput

Next you should be able to start up the server with:

    twistd -n antioch

The -n will keep it in the foreground. Configuration options are kept in the 
global settings file, *default.json*.

> The default configuration looks for a PostgreSQL server on localhost:5432 and
> a RabbitMQ-powered message queue on localhost:5672.

Running the Client
------------------

Connect to: <http://localhost:8888>

Login with username and password: `wizard/wizard`

Obviously, once in, it's a pretty good idea to change your password for the 
wizard account, which you can do with the `passwd` command.

If you'd like a more specific name for your administrator character, for the 
moment you can use:

    exec caller.set_name("My Name", real=True)

Setting the `gravatar_id` property will load a user icon for you from the 
Gravatar.com web service.

    set gravatar_id on wizard to user@example.com
