import json
from importlib import import_module
from configparser import ConfigParser
from piper.tools.shell import exists

modules = {}

def _load():
	""" load modules based on config['modules']
		modules are loaded in the same order as the entries in config
		note that dict order is officially ensured only after python 3.7
		the module which is loaded last will be regarded as main module
	"""
	config_path = 'scratch/config.json'
	
	# create or load config.json
	if exists(config_path):
		# user existing config.json
		with open(config_path, 'r') as f:
			config = json.load(f)
	
	else:
		# read config.ini and save to config.json
		config_ini = ConfigParser()
		config_ini.read('config.ini')
		config = {'modules': dict(config_ini['modules'])}
	
		# parse strings to numbers
		for section in config_ini['modules']:
			if section in config_ini:
				config[section] = {}
				for key in config_ini[section]:
					value = config_ini[section][key]
					try:
						config[section][key] = float(value) if '.' in value else int(value)
					except:
						config[section][key] = value

		# save parsed config
		with open(config_path, 'w') as f:
			json.dump(config, f, indent=4)
	
	# load modules
	for section in config['modules']:
		name = config['modules'][section]
		module = import_module('piper.%s.%s' % (section, name))
		target = getattr(module, name)(config, section)
		modules[section] = globals()[section] = target

	# use the last loaded module as the entrance to the pipeline
	setattr(modules['pipeline'], '_entrance', section)

_load()