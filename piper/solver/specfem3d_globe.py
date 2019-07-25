from math import sqrt
from piper.solver.base import base
from piper.tools.shell import call, mkdir, cp, rm, mv, read, write, exists
from piper.modules import pipeline as p

class specfem3d_globe(base):
	def setpar(self, key, val):
		def split(str, sep):
			n = str.find(sep)
			if n >= 0:
				return str[:n], str[n + len(sep):]
			else:
				return str, ''
		
		lines = []
		src = self.solver_dir + '/DATA/Par_file'
		val = str(val)
		for line in read(src).split('\n'):
			if line.find(key) == 0:
				key, _ = split(line, '=')
				_, comment = split(line, '#')
				n = len(line) - len(key) - len(val) - len(comment) - 2
				if comment:
					line = ''.join([key, '=', val, ' '*n, '#', comment])
				else:
					line = ''.join([key, '=', ' ' + val])
			
			lines.append(line)
		
		write(src, '\n'.join(lines))
	
	def setup(self):
		cp('solver/*', self.solver_dir + '/DATA')
		if not exists(self.solver_dir + '/bin/xmeshfem3D') or \
			not exists(self.solver_dir + '/bin/xspecfem3D') or \
			not exists(self.solver_dir + '/bin/xsmooth_sem'):
			print('waiting for specfem3d_globe compilation')
			call('piclean')
			exit()

	def pipe(self, mode=0):
		""" add mesher to pipeline
		"""
		if not hasattr(self, '_meshed') and \
			not exists(self.solver_dir + '/OUTPUT_FILES/addressing.txt'):
			# avoid adding mesher multiple times
			self._meshed = True
			p.add_stage(self.solver_dir, 'bin/xmeshfem3D')

		p.add_stage(self.pre_run, mode)
		p.add_stage(self.solver_dir, 'bin/xspecfem3D')
		p.add_stage(self.post_run, mode)
	
	def pipe_combine_kernels(self):
		p.add_stage(self.combine_kernels)
		p.add_stage(self.solver_dir, 'bin/xsum_kernels')
		p.add_stage(self.sum_kernels)
	
	def pre_run(self, mode=0):
		if mode == 0:
			# forward w/ save_forward = false
			self.setpar('SIMULATION_TYPE', 1)
			self.setpar('SAVE_FORWARD', '.true.')
		
		elif mode == 1:
			# forward w/ save_forward = true
			self.setpar('SIMULATION_TYPE', 1)
			self.setpar('SAVE_FORWARD', '.true.')
		
		elif mode == 2:
			# adjoint
			self.setpar('SIMULATION_TYPE', 3)
			self.setpar('SAVE_FORWARD', '.false.')

	def post_run(self, mode=0):
		if mode != 2:
			self.export_traces()
	
	def import_source(self, src):
		cp(src, self.solver_dir + '/DATA/CMTSOLUTION')
	
	def import_adjoint_source(self, src):
		cp(src, self.solver_dir + '/SEM/' + src.split('/')[-1][0:-7] + 'adj')
	
	def export_traces(self):
		mkdir('scratch/solver/traces')
		cp(self.solver_dir + '/OUTPUT_FILES/*.sem.sac', 'scratch/solver/traces')
	
	def prepare_kernel(self, src):
		kernel_dir = self.solver_dir + '/INPUT_KERNELS/%s' % src
		mkdir(kernel_dir)
		mkdir(self.solver_dir + '/OUTPUT_SUM')
		mv(self.solver_dir + '/DATABASES_MPI/*_kernel.bin', kernel_dir)
	
	def combine_kernels(self):
		# kernel module is loaded after solver module, so it can't be imported at the top of this file
		from piper.modules import kernel
		write(self.solver_dir + '/kernels_list.txt', '\n'.join(kernel.sources))

	def sum_kernels(self):
		slices = '\n'.join(str(i) for i in range(p.ntasks))
		write(self.solver_dir + '/DATA/slices.txt', slices)

		ks = []
		if kernel.alpha:
			ks.append('alpha')
		
		if kernel.beta:
			ks.append('beta')
		
		if kernel.rho:
			ks.append('rho')

		for k in ks:
			print(' - combining %s kernel' % k)
			call(('cd %s && ./bin/xcombine_vol_data_vtk DATA/slices.txt' % self.solver_dir) + \
				(' %s_kernel DATABASES_MPI OUTPUT_SUM OUTPUT_FILES 1 1' % k))
		
		mv(self.solver_dir + '/OUTPUT_FILES/*.vtk', 'output')
	
	@property
	def writable_dirs(self):
		return [self.solver_dir]