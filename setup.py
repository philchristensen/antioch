# antioch
# Copyright (c) 1999-2010 Phil Christensen
#
#
# See LICENSE for details

import ez_setup
ez_setup.use_setuptools()

import sys, os, os.path

try:
	from twisted import plugin
	from twisted.python.reflect import namedAny
except ImportError, e:
	print >>sys.stderr, "setup.py requires Twisted to create a proper antioch installation. Please install it before continuing."
	sys.exit(1)

from setuptools import setup, find_packages
from setuptools.command import easy_install
import pkg_resources as pkgrsrc

from distutils import log
log.set_threshold(log.INFO)

# disables creation of .DS_Store files inside tarballs on Mac OS X
os.environ['COPY_EXTENDED_ATTRIBUTES_DISABLE'] = 'true'
os.environ['COPYFILE_DISABLE'] = 'true'

import setup_git

def autosetup():
	pluginPackages = ['twisted.plugins', 'nevow.plugins', 'antioch.modules']
	
	dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
	sys.path.insert(0, dist_dir)
	regeneratePluginCache(pluginPackages)
	
	dist = setup(
		name			= "antioch",
		version			= "1.0",
		
		packages		= find_packages('src') + ['twisted.plugins', 'nevow.plugins'],
		package_dir		= {
			''			: 'src',
		},
		include_package_data = True,
		
		entry_points	= {
			'setuptools.file_finders'	: [
				'git = setup_git:find_files_for_git',
			]
		},
		
		test_suite		= "antioch.test",
		scripts			= ['bin/mkspace.py'],
		
		zip_safe		= False,
		
		install_requires = ['%s>=%s' % x for x in dict(
			twisted				= "10.1.0",
			nevow				= "0.10",
			psycopg2			= "2.0.14",
			simplejson			= "2.1.1",
			txamqp				= "0.3",
			ampoule				= "0.1",
			RestrictedPython	= "3.6.0",
		).items()],
		
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
							""".replace('\t', '').replace('\n', '')
	)
	
	return dist

def pluginModules(moduleNames):
	for moduleName in moduleNames:
		try:
			yield namedAny(moduleName)
		except ImportError:
			pass
		except ValueError, ve:
			if ve.args[0] != 'Empty module name':
				import traceback
				traceback.print_exc()
		except:
			import traceback
			traceback.print_exc()

def regeneratePluginCache(pluginPackages):
	print 'Regenerating plugin cache...'
	for pluginModule in pluginModules(pluginPackages):
		plugin_gen = plugin.getPlugins(plugin.IPlugin, pluginModule)
		try:
			plugin_gen.next()
		except StopIteration, e:
			pass
		except TypeError, e:
			print 'TypeError: %s' % e

if(__name__ == '__main__'):
	__dist__ = autosetup()
