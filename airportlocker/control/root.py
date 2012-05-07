import importlib
import os

import cherrypy

from eggmonster import env

# need to startup the app before importing control.urls
importlib.import_module('airportlocker.etc.startup')
from airportlocker.control.urls import api, dev
from airportlocker.lib.errors import handle_500


base = os.getcwd()

app_conf = {
	'global': {
		'script_name': '/',
	},
	'/': {
		'request.dispatch': api,
		'request.error_response': handle_500,
		'request.process_request_body': False,
	},
	'/_test': {
		'tools.staticdir.on': True,
		'tools.staticdir.root': base,
		'tools.staticdir.dir': 'test/static',
	},
}

def setupapp():
	if env.production:
		cherrypy.config.update({'environment': 'production'})
	else:
		app_conf['/_dev'] = {
			'request.dispatch': dev,
		}
	cherrypy.config.update({
		'server.socket_port': env.airportlocker_port,
		'server.socket_host': '0.0.0.0',
		'server.thread_pool': env.threads,
		'log.screen': True,
		'autoreload_on': True,
	})

def run_airportlocker():
	start_airportlocker()
	cherrypy.engine.block()

def start_airportlocker():
	setupapp()
	cherrypy.config.update(app_conf)
	cherrypy.tree.mount(None, "", config=app_conf)
	engine = cherrypy.engine
	if hasattr(engine, "signal_handler"):
		engine.signal_handler.subscribe()
	if hasattr(engine, "console_control_handler"):
		engine.console_control_handler.subscribe()
	engine.start()

if __name__ == "__main__":
	run_airportlocker()
