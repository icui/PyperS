from piper.pipeline.cluster import cluster
from piper.tools.shell import abspath

class lsf(cluster):
	@property
	def flags(self):
		""" flags used for job submission
		"""
		return '#!/bin/bash\n\n' + \
			'#BSUB -P %s\n' % self.proj + \
			'#BSUB -W %s\n' % self.walltime + \
			'#BSUB -nnodes %d\n' %  self.nnodes+ \
			'#BSUB -o output/lsf.%J.o\n' + \
			'#BSUB -e output/lsf.%J.e\n' + \
			'#BSUB -J %s\n' % self.name
	
	@property
	def jobexec(self):
		""" command for job submission
		"""
		return 'bsub'
	
	@property
	def mpiexec(self):
		""" command for running parallel task
		"""
		node_size = int(self.ntasks / self.nnodes)
		return 'jsrun -n %d -a %d -c %d -g %d' % (self.nnodes, node_size, node_size, node_size)