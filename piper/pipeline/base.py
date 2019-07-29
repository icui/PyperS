from piper.tools.module import module

class base(module):
	""" a pipeline gathers of all the tasks that will be executed
		then execute them via job script or external pipeline tools
	"""

	def add_stage(self):
		""" create a new stage which contains one task
			stages are executed in sequence
		"""
		raise NotImplementedError
	
	def add_task(self):
		""" create a new stage which contains multiple tasks and add task to this stage
			later executed add_task() will directly add task to this stage
			until another add_stage() is called
		"""
		raise NotImplementedError
	
	def submit(self):
		""" execute pipeline
		"""
		raise NotImplementedError