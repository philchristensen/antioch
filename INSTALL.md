antioch Installation
====================

by Phil Christensen
phil@bubblehouse.org

Requirements for Server
-----------------------

As long as you're using Python 2.5 or better, most recent versions of
everything else should work, but to be specific:

* [Python         >=  2.5  ](http://www.python.org)
* [PostgreSQL     >=  8.4  ](http://www.postgresql.org)
* [Twisted        >= 10.1  ](http://www.twistedmatrix.com)
* [Nevow          >=  0.10 ](http://divmod.org/trac/wiki/DivmodNevow)
* [simplejson     >=  2.1.1](http://pypi.python.org/pypi/simplejson)
* [psycopg2       >=  2.2.1](http://initd.org/psycopg)
* [txAMQP         >=  0.3  ](https://launchpad.net/txamqp)
* [ampoule        >=  0.1  ](https://launchpad.net/ampoule)

Requirements for Client
-----------------------

Pretty much any WebKit- or Mozilla-based browser should work. Opera
and Internet Exporer 6 or better should also work, but neither is
supported at this time.

* [Firefox](http://www.mozilla.com/firefox)
* [Safari](http://www.apple.com/safari)

Running the Server
-------------------

Once you install Python and Twisted, the rest will be taken care of by
the setuptools-based installer.

    python setup.py install

Next you'll need to create the default database. By default, `mkspace` tries
to connect to your PostgreSQL database as the `postgres` super-user.

    mkspace.py

This should have created the `antioch` user and a corresponding database. Next
you should be able to start up the server with:

    twistd -n antioch

The -n will keep it in the foreground.


Running the Client
------------------

Connect to: <http://localhost:8080>

Login with username and password: `wizard/wizard`

Obviously, once in, it's a pretty good idea to change your password for the 
wizard account, which you can do with the `@passwd` command.

If you'd like a more specific name for your administrator character, for the 
moment you can use:

    @exec caller.set_name("My Name", real=True)

Setting the `gravatar_id` property will load a user icon for you from the 
Gravatar.com web service.

    @set gravatar_id on wizard to user@example.com
