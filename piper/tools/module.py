import json
from piper.tools.shell import writable_dirs, exists, mkdir

class module:
	""" base class of modules provides tasks and stages to the pipeline
		each module is provided w/ a folder in ./scratch
		data is stored in ./scratch/<module_name>/data.json
		piper is blind to the implementation of the modules except for pipeline module
	"""
	def __init__(self, config, section):
		""" initialize
		"""
		# read data
		data_path = 'scratch/' + section + '/data.json'

		if exists(data_path):
			# use existing data and skip setup
			setup = False
			with open(data_path, 'r') as f:
				data = json.load(f)
			
		else:
			# create new data file and initialize module
			mkdir('scratch/' + section)
			setup = True
			data = {}
			with open(data_path, 'w') as f:
				json.dump(data, f, indent=4)
		
		# save for self.update()
		self._section = section
		self._data = data

		# add config and data to its own attribute
		if section in config:
			for key in config[section]:
				setattr(self, key, config[section][key])
		
		for key in data:
			setattr(self, key, data[key])
		
		# set writable directories
		for src in self.writable_dirs:
			writable_dirs.add(src)
		
		# call setup for newly created module
		if setup: self.setup()

	def setup(self):
		""" optional initialization method, executed before pipeline
			will not be called in restored sessions
		"""
		pass
	
	def pipe(self):
		""" method to create pipeline
		"""
		raise NotImplementedError
	
	def update(self, update):
		""" update data and save to data.ini
		"""
		# data and its storage path
		data = self._data
		data_path = 'scratch/' + self._section + '/data.json'

		# update
		for key in update:
			if update[key] == None:
				delattr(self, key)
				del data[key]

			else:
				setattr(self, key, update[key])
				data[key] = update[key]
		
		# save
		with open(data_path, 'w') as f:
			json.dump(data, f, indent=4)
	
	@property
	def writable_dirs(self):
		"""	by default only ./scratch and ./output are writable
			returns additional writable directories
		"""
		return []