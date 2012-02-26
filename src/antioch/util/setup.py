# antioch
# Copyright (c) 1999-2012 Phil Christensen
#
#
# See LICENSE for details

import sys, os, os.path, subprocess, warnings

has_git = None

postgenerate_cache_commands = ('build', 'build_py', 'build_ext',
	'build_clib', 'build_scripts', 'install', 'install_lib',
	'install_headers', 'install_scripts', 'install_data',
	'develop', 'easy_install')

pregenerate_cache_commands = ('sdist', 'bdist', 'bdist_dumb',
	'bdist_rpm', 'bdist_wininst', 'upload', 'bdist_egg', 'test')

def find_files_for_git(dirname):
	global has_git
	if(has_git is None):
		git = subprocess.Popen(['env', 'git', '--version'], stdout=subprocess.PIPE)
		git.wait()
		has_git = (git.returncode == 0)
	if(has_git):
		git = subprocess.Popen(['git', 'ls-files', dirname], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		for line in git.stdout:
			path = os.path.join(dirname, line.strip())
			yield path
	else:
		warnings.warn("Can't find git binary.")

def adaptTwistedSetup(cmd, setup_function):
	if(cmd in pregenerate_cache_commands):
		dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
		if(dist_dir not in sys.path):
			sys.path.insert(0, dist_dir)
		
		print 'Regenerating plugin cache...'
		regeneratePluginCache()

	dist = setup_function()
	if(sys.argv[-1] in postgenerate_cache_commands):
		subprocess.Popen(
			[sys.executable, '-c', 'from antioch import setup; setup.regeneratePluginCache(); print "Regenerating plugin cache..."'],
		).wait()

def pluginModules(moduleNames):
	from twisted.python.reflect import namedAny
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

def regeneratePluginCache():
	pluginPackages = ['twisted.plugins']
	
	from twisted import plugin
	
	for pluginModule in pluginModules(pluginPackages):
		plugin_gen = plugin.getPlugins(plugin.IPlugin, pluginModule)
		try:
			plugin_gen.next()
		except StopIteration, e:
			pass
		except TypeError, e:
			print 'TypeError: %s' % e

