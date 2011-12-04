antioch Installation
====================

by Phil Christensen
phil@bubblehouse.org

Requirements for Server
-----------------------

As long as you're using Python 2.5 or better, most recent versions of
everything else should work, but to be specific:

* [Python            >=  2.5  ](http://www.python.org)
* [PostgreSQL        >=  8.4  ](http://www.postgresql.org)
* [Twisted           >= 10.1  ](http://www.twistedmatrix.com)
* [Django            >=  1.3  ](http://www.djangoproject.com)
* [simplejson        >=  2.1.1](http://pypi.python.org/pypi/simplejson)
* [psycopg2          >=  2.2.1](http://initd.org/psycopg)
* [ampoule           >=  0.1  ](https://launchpad.net/ampoule)
* [RestrictedPython  >=  3.6.0](https://launchpad.net/ampoule)
* [termcolor         >=  1.1  ](http://pypi.python.org/pypi/termcolor)

If using RabbitMQ for message passing:

* [RabbitMQ       >=  2.4  ](http://www.rabbitmq.com)
* [txAMQP         >=  0.3  ](https://launchpad.net/txamqp)

If using the built-in server for message passing:

* [RestMQ                  ](https://github.com/gleicon/restmq)
* [Cyclone        >=  0.4  ](https://github.com/fiorix/cyclone)


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

This should have created the `antioch` user and a corresponding database. Next
you should be able to start up the server with:

    twistd -n antioch

The -n will keep it in the foreground. Configuration options are kept in the 
global settings file, *default.json*.

> The default configuration looks for a PostgreSQL server on localhost:5432 and
> runs a RestMQ-powered message queue on localhost:8889. However, for  better and
> scalability, RabbitMQ is recommended. It can usually be installed
> by package on most UNIXes, and via MacPorts on OS X.

Running the Client
------------------

Connect to: <http://localhost:8888>

Login with username and password: `wizard/wizard`

Obviously, once in, it's a pretty good idea to change your password for the 
wizard account, which you can do with the `@passwd` command.

If you'd like a more specific name for your administrator character, for the 
moment you can use:

    @exec caller.set_name("My Name", real=True)

Setting the `gravatar_id` property will load a user icon for you from the 
Gravatar.com web service.

    @set gravatar_id on wizard to user@example.com
