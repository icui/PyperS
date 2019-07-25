from piper.pipeline.cluster import cluster
from piper.tools.shell import abspath

class slurm(cluster):
	@property
	def flags(self):
		""" flags used for job submission
		"""
		node_size = int(self.ntasks / self.nnodes)
		flags = '#!/bin/bash\n\n' + \
			'#SBATCH --job-name=%s\n' % self.name + \
			'#SBATCH --nodes=%d\n' %  self.nnodes+ \
			'#SBATCH --ntasks-per-node=%d\n' % node_size + \
			'#SBATCH --gres=gpu:%d\n' %  node_size+ \
			'#SBATCH -o output/slurm.%J.o\n' + \
			'#SBATCH -e output/slurm.%J.e\n' + \
			'#SBATCH -t %s\n' % self.walltime
	
		if hasattr(self, 'mem'):
			flags += '#SBATCH --mem=%s\n' % self.mem
		
		return flags

	@property
	def jobexec(self):
		""" command for job submission
		"""
		return 'sbatch'
	
	@property
	def mpiexec(self):
		""" command for running parallel task
		"""
		return 'srun -n %d' % (self.ntasks)