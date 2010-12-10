#!/bin/sh

git submodule init
git submodule update
pydoctor --add-package=source/src/antioch --make-html --project-name=antioch \
	--project-url=http://philchristensen.github.com/antioch \
	--project-base-dir=/philchristensen/antioch/raw/master/ \
	--html-use-sorttable --html-use-splitlinks --html-shorten-lists \
	--html-viewsource-base=https://github.com/philchristensen/antioch/blob/master \
	--extra-system=twisted.pydoc.pkl:http://twistedmatrix.com/documents/current/api/ \
	--extra-system=nevow.pydoc.pkl:http://buildbot.divmod.org/apidocs/

