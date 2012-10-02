import os
import importlib
import logging

import yaml

import airportlocker
from . import root

def setup_logging():
	logging.basicConfig(level=logging.INFO)

def run():
	with open(os.environ['APP_SETTINGS_YAML']) as config_stream:
		airportlocker.config.update(yaml.load(config_stream))
	airportlocker.config['airportlocker_port'] = int(os.environ['PORT'])
	setup_logging()
	importlib.import_module('airportlocker.etc.startup')
	root.run()

if __name__ == '__main__':
	run()
