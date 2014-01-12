# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

import distribute_setup
distribute_setup.use_setuptools()

# disables creation of .DS_Store files inside tarballs on Mac OS X
import os
os.environ['COPY_EXTENDED_ATTRIBUTES_DISABLE'] = 'true'
os.environ['COPYFILE_DISABLE'] = 'true'

def autosetup():
	from setuptools import setup, find_packages
	return setup(
		name			= "antioch",
		version			= "2.0pre3",
		
		packages		= find_packages('src'),
		package_dir		= {
			''			: 'src',
		},
		
		# setuptools won't auto-detect Git managed files without this
		setup_requires = [ "setuptools_git >= 0.4.2", ],
		
		entry_points	= {
			# Dependencies suck, but this is definitely preferable
			# to writing everything into MANIFEST.in by hand.
			'setuptools.file_finders'	: [
				'git = setuptools_git:gitlsfiles',
			],
			'console_scripts': [
				'mkspace = antioch.scripts.mkspace:main',
			]
		},
		
		test_suite				= "antioch.test",
		include_package_data	= True,
		zip_safe				= False,
		
		# metadata for upload to PyPI
		author			= "Phil Christensen",
		author_email	= "phil@bubblehouse.org",
		description		= "a next-generation MUD/MOO-like virtual world engine",
		license			= "MIT",
		keywords		= "antioch moo lambdamoo mud game",
		url				= "https://github.com/philchristensen/antioch",
		# could also include long_description, download_url, classifiers, etc.
		long_description = """antioch is a web application for building scalable, interactive virtual worlds.
								 Begun as a MOO-like system for building virtual worlds, antioch aims to
								 take the LambdaMOO approach to creating online worlds, and update it in hopes
								 of attracting new players to an old idea.
							""".replace('\t', '').replace('\n', ''),
	)

if(__name__ == '__main__'):
	autosetup()
