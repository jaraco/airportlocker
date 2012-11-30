import logging
import importlib

import eggmonster.log_client
import pkg_resources
from cherrypy._cplogging import logfmt

import airportlocker
from . import root

def setup_logging():
	def attach_eggmonster_handler(log_id):
		log = logging.getLogger(log_id)
		handler = eggmonster.log_client.EggmonsterLogHandler(
			airportlocker.config.log_host,
			airportlocker.config.log_port,
			airportlocker.config.log_facility)
		handler.setLevel(logging.DEBUG)
		handler.setFormatter(logfmt)
		log.addHandler(handler)

	if airportlocker.config.eggmonster_error:
		attach_eggmonster_handler('cherrypy.error')

	if airportlocker.config.eggmonster_access:
		attach_eggmonster_handler('cherrypy.access')

def load_config():
	if not eggmonster.managed_env():
		eggmonster.load_local_yaml(file=pkg_resources.resource_filename(
			'airportlocker.etc', 'devel.yaml'))
	# update default config with eggmonster.env
	airportlocker.config.update(eggmonster.env)

def run():
	"""simple eggmonster entry point"""
	load_config()
	importlib.import_module('airportlocker.etc.startup')
	setup_logging()
	root.run()
