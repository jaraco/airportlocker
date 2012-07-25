import os
import importlib

import yaml
from jaraco.util.dictlib import ItemsAsAttributes

import airportlocker
from . import root

class ConfigDict(ItemsAsAttributes, dict):
	"A dictionary that provides items as attributes"

def run():
	with open(os.environ['APP_SETTINGS_YAML']) as config_stream:
		airportlocker.config = ConfigDict(yaml.load(config_stream))
	airportlocker.config['airportlocker_port'] = os.environ['PORT']
	importlib.import_module('airportlocker.etc.startup')
	root.run()

if __name__ == '__main__':
	run()
