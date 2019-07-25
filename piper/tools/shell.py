from os import path, getcwd, fsync
from subprocess import call as _call

cwd = getcwd()
writable_dirs = {'scratch', 'output'}

def call(cmd):
	if _call(cmd, shell=True):
		raise OSError('system call error: %s' % cmd)

def abspath(src):
	return src if src.startswith('/') else path.join(cwd, src)

def exists(src):
	return path.exists(abspath(src))

def check_writable(src):
	for dst in writable_dirs:
		if src.startswith(dst): return
		if src.startswith(abspath(dst)): return
	
	raise PermissionError('no permission to write to %s' % src)

def read(src):
	with open(abspath(src), 'r') as f:
		return f.read()

def write(dst, str, mode='w'):
	check_writable(dst)
	with open(abspath(dst), mode) as f:
		f.write(str)
		f.flush()
		fsync(f)

def mkdir(dst):
	check_writable(dst)
	call('mkdir -p ' + abspath(dst))

def rm(dst):
	check_writable(dst)
	call('rm -rf ' + abspath(dst))

def cp(src, dst):
	check_writable(dst)
	call('cp -r %s %s' % (abspath(src), abspath(dst)))

def mv(src, dst):
	check_writable(src)
	check_writable(dst)
	call('mv %s %s' % (abspath(src), abspath(dst)))