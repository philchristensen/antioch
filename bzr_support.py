import os.path, subprocess, warnings

has_bzr = None

def find_files_for_bzr(dirname):
	global has_bzr
	if(has_bzr is None):
		bzr = subprocess.Popen(['env', 'bzr'], stdout=subprocess.PIPE)
		bzr.wait()
		has_bzr = (bzr.returncode == 0)
	if(has_bzr):
		# loop to yield paths that start with `dirname`
		bzr = subprocess.Popen(['bzr', 'ls', '-vR', dirname], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		for line in bzr.stdout:
			if(line.strip().startswith('V')):
				path = os.path.join(dirname, line.split()[1].lstrip('/'))
				yield path
	else:
		warnings.warn("Can't find bzr binary.")

