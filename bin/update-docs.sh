#!/bin/sh

pydoctor --add-package=source/src/antioch \
	--make-html --project-base-dir=source/src \
	--extra-system=twisted.pydoc.pkl:http://twistedmatrix.com/documents/current/api/ \
	--extra-system=nevow.pydoc.pkl:http://buildbot.divmod.org/apidocs/

