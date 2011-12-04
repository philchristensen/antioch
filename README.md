antioch 1.0
===========

17 September 2010

by Phil Christensen

`mailto:phil@bubblehouse.org`

Introduction
-------------

antioch is a web application for building scalable, interactive virtual
worlds.

Begun as a MOO-like system for building virtual worlds, the goal was to
take the LambdaMOO approach to creating online worlds, and update it in hopes
of attracting new players to an old idea.

Like many MOO-clones before it, antioch uses Python as its internal scripting
language. This provides a powerful environment for game authors, while a 
flexible object model allows for creation of complex in-game objects.

Universe data is saved in a PostgreSQL database, and all database code (aka, 
'verbs') run inside their own subprocess (each in a separate database transaction), allowing a degree of isolation between verb execution.

Additionally, the in-universe messaging layer is implemented in RabbitMQ. 
Combined with database replication and webserver load-balancing, this provides 
unmatched possibilities for operating large-scale deployments.

Feature Set
-----------

* **Customizable AJAX-Enabled Client** — 
  The antioch web client provides a standards-compliant interface based
  on Django and jQuery, and is supported by all modern browsers.
  
  Although the default database provided is geared towards text-based games,
  the flexibility of the client interface and the power of the plugin system
  allows many different kinds of games to be developed on the antioch 
  platform.

* **Graphical Object Editors** — 
  Programmers and authors alike will find the built-in authoring tools
  expedite world creation and verb programming.

* **Plugin System** — 
  antioch 'modules' allow developers to create new client functionality.
  The module system was used to implement the built-in object and verb 
  editors, demonstrating the creation of new verb-environment functions,
  Web resources, and client-side JavaScript.

* **Isolated Verb Execution** — 
  Database code is run in individual subprocesses, allowing for memory and
  runtime limits to be applied at the UNIX process level, and allowing for
  verb code to be written in a synchronous style.

* **Highly Scalable Messaging Layer** — 
  antioch uses the RabbitMQ server to implement message passing support, allowing support of thousands of active clients with minimal latency.

* **Powerful Natural-Language Parser** — 
  The built-in interpreter parses a large number of different imperative
  statements, making user-world interaction a more immersive experience.

* **Internal Scripting** — 
  A Pure-Python scripting layer integrates tightly with the framework code,
  allowing a high degree of customization.
  
* **Robust Networking** — 
  antioch relies on the Twisted Python and Django frameworks to implement
  applicationn server communication. This robust asynchronous networking library
  allows client counts to scale easily to hundreds of connections.


Copyright
---------

All code in this distribution is (C) Phil Christensen, except
CodePress, Copyright (C) Fernando M.A.d.S. <fermads@gmail.com>

antioch is made available under the MIT/X Consortium license.
The included LICENSE file describes this in detail.
