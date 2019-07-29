from piper.pipeline.cluster import cluster
from piper.tools.shell import exists, write, call

class slurm(cluster):
	def submit(self):
		""" create and submit job script
		"""
		# create job script
		job_path = 'scratch/pipeline/job.bash'
		
		if not exists(job_path):
			# flags for job submission
			node_size = int(self.ntasks / self.nnodes)
			script = '#!/bin/bash\n\n' + \
				'#SBATCH --job-name=%s\n' % self.name + \
				'#SBATCH --nodes=%d\n' %  self.nnodes+ \
				'#SBATCH --ntasks-per-node=%d\n' % node_size + \
				'#SBATCH --gres=gpu:%d\n' %  node_size + \
				'#SBATCH -o output/slurm.%J.o\n' + \
				'#SBATCH -e output/slurm.%J.e\n' + \
				'#SBATCH -t %s\n' % self.walltime
		
			if hasattr(self, 'mem'):
				script += '#SBATCH --mem=%s\n' % self.mem
			
			# load modules
			if hasattr(self, 'modules'):
				script += '\nmodule load %s\n' % self.modules
			
			# command before execution
			if hasattr(self, 'pre_exec'):
				script += '\n%s\n' % self.pre_exec
			
			# execute stages
			script += '\npython -c "from piper.modules import pipeline; pipeline.loop()"\n'
			
			# command after execution
			if hasattr(self, 'post_exec'):
				script += '\n%s\n' % self.post_exec

			# write job script
			write(job_path, script)

		# submit job
		call('sbatch ' + job_path)
	
	def mpiexec(self, cmd):
		""" command for running parallel task
		"""
		if cmd.startswith('python'):
			return 'mpirun -n %d %s' % (self.ntasks, cmd)
		else:
			return 'srun %s' % cmd