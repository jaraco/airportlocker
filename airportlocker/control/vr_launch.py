import os
import importlib

import yaml

import airportlocker
from . import root

def run():
	with open(os.environ['APP_SETTINGS_YAML']) as config_stream:
		airportlocker.config.update(yaml.load(config_stream))
	airportlocker.config['airportlocker_port'] = os.environ['PORT']
	importlib.import_module('airportlocker.etc.startup')
	root.run()

if __name__ == '__main__':
	run()
