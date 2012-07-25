import os
import importlib

import pkg_resources
import cherrypy
import fab

import airportlocker
from airportlocker.lib.errors import handle_500


base = os.getcwd()

app_conf = {
	'global': {
		'script_name': '/',
	},
	'/': {
		'request.dispatch': None,
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
	fab.config['base'] = pkg_resources.resource_filename('airportlocker', '')
	# import urls after base is set (because templates fail to load otherwise)
	urls = importlib.import_module('airportlocker.control.urls')
	app_conf['/']['request.dispatch'] = urls.api
	if airportlocker.config.production:
		cherrypy.config.update({'environment': 'production'})
	else:
		app_conf['/_dev'] = {
			'request.dispatch': urls.dev,
		}
	cherrypy.config.update({
		'server.socket_port': airportlocker.config.airportlocker_port,
		'server.socket_host': '0.0.0.0',
		'server.thread_pool': airportlocker.config.threads,
		'log.screen': True,
		'autoreload_on': True,
	})

def run():
	start()
	cherrypy.engine.block()

def start():
	setupapp()
	cherrypy.config.update(app_conf)
	cherrypy.tree.mount(None, "", config=app_conf)
	engine = cherrypy.engine
	if hasattr(engine, "signal_handler"):
		engine.signal_handler.subscribe()
	if hasattr(engine, "console_control_handler"):
		engine.console_control_handler.subscribe()
	engine.start()
