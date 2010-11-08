import os, os.path, subprocess, warnings

has_git = None

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

