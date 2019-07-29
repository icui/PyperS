from piper.pipeline.cluster import cluster
from piper.tools.shell import exists, write, call

class lsf(cluster):
	def submit(self):
		""" create and submit job script
		"""
		# create job script
		job_path = 'scratch/pipeline/job.bash'
		
		if not exists(job_path):
			# flags for job submission
			node_size = int(self.ntasks / self.nnodes)
			script = '#!/bin/bash\n\n' + \
				'#BSUB -P %s\n' % self.proj + \
				'#BSUB -W %s\n' % self.walltime + \
				'#BSUB -nnodes %d\n' %  self.nnodes+ \
				'#BSUB -o output/lsf.%J.o\n' + \
				'#BSUB -e output/lsf.%J.e\n' + \
				'#BSUB -J %s\n' % self.name
			
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
		call('bsub ' + job_path)
	
	def mpiexec(self, cmd):
		""" command for running parallel task
		"""
		node_size = int(self.ntasks / self.nnodes)
		return 'jsrun -n %d -a %d -c %d -g %d %s' % (self.nnodes, node_size, node_size, node_size, cmd)