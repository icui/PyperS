from math import sqrt
from glob import glob
from piper.solver.base import base
from piper.tools.shell import call, mkdir, cp, rm, mv, read, write, exists
from piper.modules import pipeline as p, modules

class specfem3d_globe(base):
	def setpar(self, key, val):
		""" modify DATA/Par_file in specfem3d_globe
		"""
		def split(str, sep):
			n = str.find(sep)
			if n >= 0:
				return str[:n], str[n + len(sep):]
			else:
				return str, ''
		
		lines = []
		src = 'scratch/solver/DATA/Par_file'
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
	
	def check_binary(self, bin_file):
		""" ensure required binary exists
			if not, exit and wait for compilation
		"""
		if not exists('scratch/solver/bin/' + bin_file):
			print('waiting for specfem3d_globe compilation')
			# clear current pipeline
			rm('scratch')
			rm('output')
			exit()
	
	def setup(self):
		""" link specfem3d_globe subdirectories to scratch/solver
		"""
		call('ln -s %s scratch/solver' % (self.solver_dir + '/bin'))
		call('ln -s %s scratch/solver' % (self.solver_dir + '/DATA'))
		call('ln -s %s scratch/solver' % (self.solver_dir + '/OUTPUT_FILES'))
		call('ln -s %s scratch/solver' % (self.solver_dir + '/DATABASES_MPI'))
		call('ln -s %s scratch/solver' % (self.solver_dir + '/SEM'))
		cp('Par_file', 'scratch/solver/DATA')
		cp('STATIONS', 'scratch/solver/DATA')
		cp('STATIONS', 'scratch/solver/DATA/STATIONS_ADJOINT')
		
		# set dimension
		nproc = int(sqrt(p.ntasks / 6))
		self.setpar('NPROC_XI', nproc)
		self.setpar('NPROC_ETA', nproc)

	def pipe(self, src, mode=0):
		""" add solver to pipeline
			call mesher if no addressing.txt is found
		"""
		# call mesher if necessary
		if not hasattr(self, '_meshed') and \
			not exists('scratch/solver/OUTPUT_FILES/addressing.txt'):
			# check and call mesher
			self.check_binary('xmeshfem3D')
			p.add_stage('scratch/solver', 'bin/xmeshfem3D')

			# avoid adding mesher multiple times
			self._meshed = True

		# check and call solver
		self.check_binary('xspecfem3D')
		p.add_stage(self.pre_run, src, mode)
		p.add_stage('scratch/solver', 'bin/xspecfem3D')
		p.add_stage(self.post_run, src, mode)
	
	def pipe_export_kernels(self):
		""" sum and smooth kernels, then combine them into vtk files
		"""
		# check tomo binaries
		self.check_binary('xsmooth_sem')
		self.check_binary('xsum_kernels')
		self.check_binary('xcombine_vol_data_vtk')

		kernels = modules['kernel'].kernels
		sources = modules['kernel'].sources

		# prepare kernel list for summing kernels
		write('scratch/solver/kernels_list.txt', '\n'.join(sources))
		
		# prepare slice list for combining kernels
		slices = '\n'.join(str(i) for i in range(p.ntasks))
		write('scratch/solver/slices.txt', slices)

		# sum kernels
		kernel_names = ','.join((kernel + '_kernel') for kernel in kernels)
		p.add_stage('scratch/solver', 'bin/xcombine_sem', kernel_names, 'kernels_list.txt', 'DATABASES_MPI')
		
		# # smooth kernels
		# for kernel in kernels:
		# 	p.add_stage('scratch/solver', 'bin/xsmooth_sem', self.smooth, self.smooth, kernel + '_kernel', 'DATABASES_MPI', 'DATABASES_MPI')

		# combine kernels
		for kernel in kernels:
			p.add_task(self.combine_kernel, kernel)
	
	def pre_run(self, src, mode):
		# copy source to solver direcotory
		cp('events/%s/CMTSOLUTION' % src, 'scratch/solver/DATA/CMTSOLUTION')

		if mode == 0:
			# set par_file to forward w/ save_forward = false
			self.setpar('SIMULATION_TYPE', 1)
			self.setpar('SAVE_FORWARD', '.true.')
		
		elif mode == 1:
			# set par_file to forward w/ save_forward = true
			self.setpar('SIMULATION_TYPE', 1)
			self.setpar('SAVE_FORWARD', '.true.')
		
		elif mode == 2:
			# copy adjoint sources
			adjoint_sources = glob('scratch/kernel/%s/*' % src)
			for adsrc in adjoint_sources:
				cp(adsrc, 'scratch/solver/SEM/' + adsrc.split('/')[-1][0:-7] + 'adj')
			
			# set par_file to adjoint
			self.setpar('SIMULATION_TYPE', 3)
			self.setpar('SAVE_FORWARD', '.false.')

	def post_run(self, src, mode):
		""" export traces in forward mode
			export kernel in adjoint mode
		"""
		# create directory for output
		mkdir('scratch/solver/' + src)

		if mode == 2:
			# export kernels in adjoint mode
			mv('scratch/solver/DATABASES_MPI/*_kernel.bin', 'scratch/solver/' + src)
		
		else:
			# export traces in forward mode
			mv('scratch/solver/OUTPUT_FILES/*.sem.sac', 'scratch/solver/' + src)
	
	def combine_kernel(self, kernel):
		""" combine kernel to a single vtk file
		"""
		call('cd scratch/solver && ./bin/xcombine_vol_data_vtk slices.txt ' + kernel + \
			'_kernel DATABASES_MPI DATABASES_MPI OUTPUT_FILES 1 1')
		
		mv('scratch/solver/OUTPUT_FILES/*.vtk', 'output')