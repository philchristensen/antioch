antioch 2.0pre3
=================

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

* Flexible plugin system, highly scalable execution layour using Celery and RabbitMQ


antioch is made available under the MIT/X Consortium license.

The included LICENSE file describes this in detail.
