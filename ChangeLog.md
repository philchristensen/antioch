2012-02-26    Phil Christensen <phil@bubblehouse.org>

* Another massive set of refactorings
* Client interface and plugin system now Django-based
* Messaging revamped, standardized on RabbitMQ and Pika
* Implemented queue-based appserver access
* Logging improved, standardized on using Python logging
* Appserver split from web client process
* Developed Heroku-/Foreman-compatible architecture

2011-06-19    Phil Christensen <phil@bubblehouse.org>

* Renamed txspace to antioch
* Support for in-memory local messaging server
* Implemented runtime limits and installed Zope's RestrictedPython
* Verbs can now be backed by files on disk, and reloaded on the fly
* Added delayed task support to verb environment
* Created 'ask' plugin, demonstrating out-of-band plugins
* Registration module for email verified accounts
* JSON-based external configuration file
* Guest support for anonymous trial users
* Banlists and alternate authentication sources
* Numerous additional verbs in default universe
* Client Gravatar.com support
* More documentation work
* Testing and deployment improvements
* Colorized log output and removed spurious messages

2010-09-01    Phil Christensen <phil@bubblehouse.org>

* Massive rewrites for most of the codebase.
* Shared-nothing deployment architecture
* Objects loaded from PostgreSQL database
* Simple system for spawning new databases
* Message passing occurs via RabbitMQ server
* Verbs run synchronously inside child processes
* Created module system for extending GUI
* Object editors re-styled and cleaned up, implemented as module
* Using jQuery UI, both jQuery libs loaded from Google CDN

2009-09-14    Phil Christensen <phil@bubblehouse.org>

* Enhanced information returned to client for contents list.
Split into players and contents, added support for player
icons, better mood/away message support
* Implemented command-line history support in web client
* Polished login page
* Began using jQuery for client-side code
* Improved editor error handling
* Reorganized assets directory
* Implemented reload support for editor windows
* Migrated client, verb and property layouts to pure CSS
* Switched to using CodeMirror syntax highlighting
* Standardized on unicode strings
* Improved test coverage
* Improved error handling and reporting for user code
* Refactored Verb and Property classes
* Revised webclient contents display, autolook on connect
* Much editor refactoring
* Introduced the Q context for system-initiated code
* Made web session support more robust, using txOpenID session tech
* All entities now keep a reference to the registry they are from
* Removed auth module
* Removed cocoa client and PB stuff, focusing on web client

2008-07-11    Phil Christensen <phil@bubblehouse.org>

* Renamed to txSpace and moved to Bazaar hosting on Launchpad
* changed to MIT license
* converted editors to use inlineCallbacks for clarity, moved some things 
  out of auth and into actions
* implemented entity contexts to allow for multithreaded verb code, and 
  simpler protocol implementation.
* moved client code into separate package
* Created new 'assets' package for easy access to templates, verbs, and 
  web support files; Removed old SVN Id tags; simplified resources by 
  removing unnecessary locateChild() methods; removed broken and unused 
  setup.py; athena exposure changed to use decorators
* moved tests into core package
* massive refactoring of server plugin, portals, auth framework, comments, 
  cleanup, etc, etc, etc
* cleaned up test directory, added function to get the default verb 
  directory from inner.space
* persistence bug (#26) should be fixed now. note that repr() for entities 
  has changed, into something that could be eval'ed in a internal 
  environment, e.g., get_global('#2 (Wizard)')
* removed a ton more cruft like old or useless comments, and removed some 
  retardation from pbclient
* some cleanup, and removal of old ssl support cruft
* Fixed authenticate so it properly stores created guest accounts, 
  modified author_dig to be more robust, added exceptions to verb 
  environment, fixed some errors in ACLs, other small things...
* Implemented ban lists for webclient, and implemented guest mechanism, 
  but it either causes or exposes some weird, weird bug

2007-02-11    Phil Christensen <phil@bubblehouse.org>

* Created Athena-based AJAX web client
* Completed initial unicode conversion. Editing and observations
  now pass only unicode dictionaries
* Updated to a new, non-TAP plugin method.
* Moved property and verb to their own modules, in hopes of making
  entity a bit less unweildy. Updated tests and fixed a few
  outstanding bugs. Also replaced use of authUser global variable
  directly with get/set_current_user() functions, in preparation
  of work on bug #16
* Added is_connected_player() check in auth mechanism. Attempts
  to log in a second time will fail as if the credentials were
  incorrect.
* Now properly stripping slashes from quoted strings.
* Removed debugging code from test and modified test_bug_9 to
  test the true issue, slashes....
* XML Persistence on shutdown implemented, still need a little
  cleanup of first/subsequent run process...
* Made the possibly dangerous sudo command a bit more useful...
* Updated ACL unit test...
* Much cleanup and support for login/logout events and connection
  refusal
* Implemented 'authenticate' hook to enable guest capability.
* Made some changes to fix loading bug with eval'd properties
* Fixed some bugs in import export process, beefed up test
* Added some checks to entity to catch particular kinds of recurision
  when they happen...also added some dummy functions to the webclient...
* Removed the Java and Cocoa clients, now focusing support on the web
  client. PB support will remain for the time being, but will break
  compatibility with the deprecated clients -- all data passed back
  and forth via Athena or PB will use exclusively unicode strings.
* Removed java client support scripts.
* Updated registry test to test Unnamed object parsing (-1 ids now
  return None), fixed a bug in entity editor, created stubs for verb
  editor, other tweaks
* Removed old server scripts, replaced by "twistd txspace"

2006-04-02    Phil Christensen <phil@bubblehouse.org>

* modified some settings for syntax highlighting
* fixed parser bug with posessives
* fixed some bugs in load/reload verb feature
* fixed bug with saved user login info
* added exit alias feature/verb

2006-04-01    Phil Christensen <phil@bubblehouse.org>

* fixed a million bugs
* removed 'image' feature for the time being
* added preferences support to save last connection info (only half works)
* activated copy/cut/paste in verb editor

2006-01-03  Phil Christensen <phil@bubblehouse.org>

* finished implementing SSH interface. now wizards
  can connect with their txspace password via
  ssh to a manhole instance running on port 4040

2006-01-01  Phil Christensen <phil@bubblehouse.org>

* bootstrap_server.py can now accept 'datafile' argument to
  load xml datafile
* created @export command for wizards to export current registry

2005-12-31  Phil Christensen <phil@bubblehouse.org>

* finished implementation of XML import/export functionality
* modified txspace/bigbang.py to create a telnet interface
  on port 4040 for debugging purposes. intent is to eventually
  provide conch-enabled login via regular ssh client which
  would authenticate via registry using existing Portal.
* modified bootstrap_server.py to accept additional arguments,
  passed to twistd.
* updated copyright and added subversion Id keyword to all files

2005-12-01  Phil Christensen <phil@bubblehouse.org>

* began implementing XML export/import

2005-11-29  Phil Christensen <phil@bubblehouse.org>

* restructured codebase (moving bin into inner)

2005-07-27  Phil Christensen <phil@bubblehouse.org>

* implemented partially functional appleevent support
  in cocoa client, with the intent of adding 'external
  editor' support.

2005-07-23  Phil Christensen <phil@bubblehouse.org>

* moved get_environment function to code module, all prep of
  execution environment happens there
* if a verb has its is_method property set (i.e. as a keyword
  argument to add_verb), the parser will ignore it as a verb
  choice, so it can only be executed programmatically
* added 'sudo' method which runs a function as the owner
  of the current verb

2005-07-10  Phil Christensen <phil@bubblehouse.org>

* removed 'is' as a preposition from lexer/parser
* finished basic functionality of cocoa client
* some documentation
* updated copyright notice
* moved default verbs into own directory, now loaded
  by helper function in minimal.py

2005-07-03  Phil Christensen <phil@bubblehouse.org>

* fixed issue with ambiguous verbs by adding
  'is_ability' flag to add_verb
* implemented verb code caching
* moved get_environment to code module from parser
* changed mechanism for setting default acl. now
  we can pass an 'acl_config' parameter to add_verb,
  add_property, or Entity(). this is a function object
  that is called with the acl instance of the specified
  object.
* modified @dig to create rooms inheriting from class_room
  (by getting a 'default_room_class' property from the
  system object)
* modified new_obj in execution environment to allow
  hooks for quotas, etc

2005-05-24  Phil Christensen <phil@bubblehouse.org>

* rewrote ACL editor to work with new scheme

2005-05-23  Phil Christensen <phil@bubblehouse.org>

* completely refactored ACL system
* ACLs are now part of the standard object, not
  a secondary class, although the security module
  still exists and has functions to manage ACLs
* reordered methods in entity
* fixed bug due to moving editor code
* made 'owner' a part of the standard object def

2005-03-20  Phil Christensen <phil@bubblehouse.org>

* moved editor code into separate module.
* removed "legacy" attr hooks

2005-02-25  Phil Christensen <phil@bubblehouse.org>

* fixed bug in acl class (re: new users)
* realized the severe problems with ACL class

2005-02-24  Phil Christensen <phil@bubblehouse.org>

* created applet to allow web-based use of the client.

2004-12-15  Phil Christensen <phil@bubblehouse.org>

* created a basic room class (class_room, haha), with darkness
* moved code to supply observations to client into verbs on
  class_room and system object
* created the beginning of the getting started guide
* bugfixes and documentation

2004-12-06  Phil Christense <phil@bubblehouse.org>

* updated documentation, finally began README file

2004-12-05  Phil Christensen <phil@bubblehouse.org>

* changed observations mechanism to only update
  for connected players
* fixed intermittent bug where after login, no
  client window would appear (due to calling a
  remote method on the client during the login
  phase)
* changed method for creating minimal db, so that
  predefined verbs contain source code as well
* implemented say, hear, @adduser, go, @dig, @tunnel
* modified build script, omitted automatic testing,
  moved java build to ./build_client.py
* changed bootstrap-server.py to run without arguments,
  it now only builds the server txspace.tap file
* added run-server.py to automatically run the most recent
  tap file

2004-08-18  Phil Christensen <phil@bubblehouse.org>

* finished Property/Verb/Entity/ACL editor interactions

2004-08-10  Phil Christensen <phil@bubblehouse.org>

* made Property editor more functional with dynamic types, etc.
* Began implementing ACL editor
* created @acl verb

2004-08-09  Phil Christensen <phil@bubblehouse.org>

* added bin/bootstrap-server.py script for dev purposes. allows
  easier ecplise integration, and builds new tap file for each 
  launch.
* finished basic entity editor functionality
* created ACLError as subclass of PermissionError, PermissionError
  is more abstract now, takng single message in constructor;
  changed usage of PermissionError to ACLError when appropriate.
* modified Entity to keep user type as integer, rather than booleans
* added code to restore auth.lastUser upon deferred callback
* added requestor methods to client/server to allow client request
  of entity/verb/property editor windows (needed to support entity window)
* added property editor window, supports property definition by string,
  eval, and pickle forms.
* added r_exec/r_eval methods to code.py to have central location for
  code execution, in hopes of securing interface when possible.

2004-08-06  Phil Christensen <phil@bubblehouse.org>

* updated client to support asynchronous results
* converted CodeEditor to non-modal window
* added PrimitiveMapWrapper class to provide cleaner
  interface when working with PrimitiveMaps and unicode.
* fixed and re-implemented beginings of new object editor,
  featuring new object browser.

2004-08-04  Phil Christensen <phil@bubblehouse.org>

* began work on remote object browser
* fixed some issues with entity.py and client
  brought about by new ACL scheme.

2004-01-25  Phil Christensen <phil@bubblehouse.org>

* added handler for ispace:// URL scheme

2004-01-22  Phil Christensen <phil@bubblehouse.org>

* removed shady Mac OS X app bundle build code from setup.py

2004-01-13  Phil Christensen <phil@bubblehouse.org>

* finished adding acl support to entity/verb/property
* updated unit tests for new ACL framework
* modified PermissionError class to provide extended functionality with ACLs
* temporarily removed Mac OS X app bundle support from build routines

2003-12-29  Phil Christensen <phil@bubblehouse.org>

* added '_acl' property to Entity class
* created ACL/security modules
* implemented unit tests for registry.py, parser.py, and security.py

2003-12-23  Phil Christensen <phil@bubblehouse.org>

* officially adopted GNU Public License, added copyright info
* created new parser with extended syntax capabilities
* enhanced Verb functionality for developers
* support for "core" packages via twisted plugin mechanism
* dynamic per-object observations implemented
* implemented distutils build system

2003-11-10  Phil Christensen <phil@bubblehouse.org>

* merged 0.6 trunk with 0.5.1 trunk.
* underlying network protocol changed to twisted/PB
* massive refactoring in txspace/entity.py 
  (formerly known as txspace/object.py)
