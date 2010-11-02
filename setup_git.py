import os.path, subprocess, warnings

has_git = None

def find_files_for_git(dirname):
	global has_git
	if(has_git is None):
		git = subprocess.Popen(['env', 'git'], stdout=subprocess.PIPE)
		git.wait()
		has_git = (git.returncode == 0)
	if(has_git):
		git = subprocess.Popen(['git', 'ls', '-vR', dirname], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		for line in git.stdout:
			if(line.strip().startswith('V')):
				basename = line.split()[1].lstrip('/')
				path = os.path.join(dirname, basename)
				yield path
	else:
		warnings.warn("Can't find git binary.")

