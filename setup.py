# antioch
# Copyright (c) 1999-2011 Phil Christensen
#
#
# See LICENSE for details

import distribute_setup
distribute_setup.use_setuptools()

try:
	from twisted import plugin
except ImportError, e:
	import sys
	print >>sys.stderr, "setup.py requires Twisted to create a proper antioch installation. Please install it before continuing."
	sys.exit(1)

from distutils import log
log.set_threshold(log.INFO)

# disables creation of .DS_Store files inside tarballs on Mac OS X
import os
os.environ['COPY_EXTENDED_ATTRIBUTES_DISABLE'] = 'true'
os.environ['COPYFILE_DISABLE'] = 'true'

def autosetup():
	from setuptools import setup, find_packages
	return setup(
		name			= "antioch",
		version			= "1.0",

		packages		= find_packages('src') + ['twisted.plugins'],
		package_dir		= {
			''			: 'src',
		},

		entry_points	= {
			'setuptools.file_finders'	: [
				'git = antioch.util.setup:find_files_for_git',
			],
			'console_scripts': [
				'mkspace = antioch.scripts.mkspace:main',
			]
		},

		test_suite				= "antioch.test",
		include_package_data	= True,
		zip_safe				= False,

		install_requires = ['%s%s' % x for x in {
			'twisted'			: ">=10.1.0",
			'django'			: '>=1.3',
			'psycopg2'			: "==2.4.1",
			'simplejson'		: ">=2.1.1",
			'txamqp'			: ">=0.3",
			'ampoule'			: ">=0.1",
			'RestrictedPython'	: ">=3.6.0",
			'termcolor'			: ">=1.1.0",
			'cyclone'			: ">=0.4",
			# 'restmq'			: ">=1.0",
		}.items()],
		
		# dependency_links = [
		# 	"http://github.com/philchristensen/restmq/tarball/master#egg=restmq-1.0",
		# ],

		# metadata for upload to PyPI
		author			= "Phil Christensen",
		author_email	= "phil@bubblehouse.org",
		description		= "a MOO-like system for building virtual worlds",
		license			= "MIT",
		keywords		= "antioch moo lambdamoo mud game",
		url				= "https://github.com/philchristensen/antioch",
		# could also include long_description, download_url, classifiers, etc.
		long_description = """antioch is a web application for building scalable, interactive virtual worlds.
								 Begun as a MOO-like system for building virtual worlds, the goal was to
								 take the LambdaMOO approach to creating online worlds, and update it in hopes
								 of attracting new players to an old idea.
							""".replace('\t', '').replace('\n', ''),
	)

if(__name__ == '__main__'):
	import sys
	sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
	
	from antioch.util.setup import adaptTwistedSetup
	adaptTwistedSetup(sys.argv[-1], autosetup)
