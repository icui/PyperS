import json
from sys import stderr
from piper.tools.shell import call, cwd, write, exists, mkdir
from piper.pipeline.base import base
from piper.modules import modules

def _align(i, total):
		""" align integer output to same digits
		"""
		ndigits = len(str(total))
		istr = str(i + 1)
		while len(istr) < ndigits:
			istr = '0' + istr
		
		return istr

def _serialize(args):
		""" convert function to object name and function name
			return
				for external binary: {'bin': [directory, file], 'args'}
				for internal function: {'func': [module, method], 'args'}
		"""
		if len(args) == 0:
			# new stage for future tasks
			return []
		
		elif type(args[0]) == str:
			# external binary
			return {'bin': args[0: 2], 'args': args[2:]}
		
		else:
			# internal function
			cmd = args[0].__name__
			for section in modules:
				if modules[section] == args[0].__self__: break
			
			return {'func': [section, cmd], 'args': args[1:]}

class cluster(base):
	""" base class for cluster based pipeline
		executed by calling pipeline.loop() / pipeline.loop_mpi() in job script
	"""
	def pipe(self):
		""" gathers modules, stages and tasks and write to data.json
			if data.json exists, use it instead
		"""
		stages_path = 'scratch/pipeline/stages.json'
		if not exists(stages_path):
			# temp array to collect stages and tasks and save to self.stage
			self._stages = []
			modules[self._entrance].pipe()

			# initialize
			self.update({'stage': 0, 'failed_tasks': []})
			with open(stages_path, 'w') as f:
				json.dump(self._stages, f, indent=4)

	def submit(self):
		""" create and submit job script
			use existing job script if available
		"""
		# create job script
		job_path = 'scratch/pipeline/job.bash'
		
		if not exists(job_path):
			# flags for job submission
			script = self.flags

			# load modules
			if (hasattr(self, 'modules')):
				script += '\nmodule load %s\n' % self.modules
			
			# preprocess
			if hasattr(self, 'pre_exec'):
				script += '\n%s\n' % self.pre_exec
			
			# execute stages
			script += '\npython -c "from piper.modules import pipeline; pipeline.loop()"\n'
			
			# postprocess
			if hasattr(self, 'post_exec'):
				script += '\n%s\n' % self.post_exec

			# job script
			write(job_path, script)

		# submit job
		call('%s %s' % (self.jobexec, job_path))
	
	def add_stage(self, *args):
		""" creates a single task stage executed in first node
		"""
		self._stages.append(_serialize(args))

	def add_task(self, *args):
		""" creates a multi task stage executed in all nodes
		"""
		# add a new stage for future tasks
		if len(self._stages) == 0 or type(self._stages[-1]) != list:
			self.add_stage()
		
		self._stages[-1].append(_serialize(args))
	
	def loop(self):
		""" main function called by job script
			execute all stages
		"""
		# read stages
		with open('scratch/pipeline/stages.json', 'r') as f:
			stages = json.load(f)
		
		nstages = len(stages)

		# execute stages
		while self.stage < nstages:
			stage = stages[self.stage]
			# convert parallel stages w/ only one task to serial stage
			if type(stage) == list and len(stage) == 1:
				stage = stage[0]
			
			# output message
			msg = '%s / %d' % (_align(self.stage, nstages), nstages)
			if type(stage) == list:
				# parallel stage
				print(msg)
				call(self.mpiexec + ' python -c "from piper.modules import pipeline; pipeline.loop_mpi()"\n')
			
			else:
				args = stage['args']
				# head node stage
				if 'func' in stage:
					# internal function
					section, cmd = stage['func']
					print(msg + '  %s.%s(%s)' % (section, cmd, ', '.join(str(arg) for arg in args)))
					getattr(modules[section], cmd)(*args)
				
				else:
					# external binary
					bin_dir, bin_file = stage['bin']
					argstr = ' '.join(str(arg) for arg in args)
					print(msg + '  %s %s' % (bin_file, argstr))
					call('cd %s && %s %s %s' % (bin_dir, self.mpiexec, bin_file, argstr))

			self.update({'stage': self.stage + 1})
		
		print('done')

	def loop_mpi(self):
		""" called by self.loop()
			execute parallel internal functions
		"""
		# init mpi
		from mpi4py import MPI
		comm = MPI.COMM_WORLD
		rank = self.rank = comm.Get_rank()

		# read stages
		with open('scratch/pipeline/stages.json', 'r') as f:
			stages = json.load(f)
		
		# ensure current stage is parallel
		stage = stages[self.stage]
		if type(stage) != list or len(stage) <= 1:
			print('wrong mpi call', file=stderr)
			exit(-1)
		
		# index of the tasks to be executed
		stage_size = len(stage)
		taskids = self.failed_tasks if len(self.failed_tasks) else list(range(stage_size))

		# number of failed tasks
		status = 0
		
		# execute tasks
		failed = []
		for j in taskids:
			# self.ntasks := total number of processes
			# rank := index of current process
			if j % self.ntasks == rank:
				# assign task to current process
				try:
					args = stage[j]['args']
					section, cmd = stage[j]['func']
					print(' - task %s on proc_%s: %s.%s(%s)' % (_align(j, stage_size),
						_align(j % self.ntasks, self.ntasks), section, cmd, ', '.join(str(arg) for arg in args)))
					getattr(modules[section], cmd)(*args)
		
				except Exception as e:
					print(e, file=stderr)
					failed.append(j)
		
		# collect failed tasks
		failed_gather = comm.gather(failed, root=0)
		if rank == 0:
			failed = []
			for node in failed_gather:
				for taskid in node:
					print(' * task %s failed' % _align(taskid, stage_size))
					failed.append(taskid)
			
			status = len(failed)
			self.update({'failed_tasks': failed})
		
		# broadcast error status
		status = comm.bcast(status, root=0)
		if status:
			exit(status)
	
	@property
	def flags(self):
		""" flags used for job submission
		"""
		raise NotImplementedError
	
	@property
	def jobexec(self):
		""" command for job submission
		"""
		raise NotImplementedError
	
	@property
	def mpiexec(self):
		""" command for running parallel task
		"""
		raise NotImplementedError