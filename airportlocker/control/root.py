import airportlocker.etc.startup

import os

import cherrypy

from pmxtools.erroremail import email_error, email_pdl_errors
from eggmonster import env

from airportlocker.control.urls import api, dev
from airportlocker.lib.errors import handle_500


base = os.getcwd()

app_conf = {
	'global': {
		'script_name': '/',
	},
	'/' : {
        'request.dispatch': api,
        'request.error_response': handle_500,
        'request.process_request_body': False,
	},
	'/_test' : {
		'tools.staticdir.on': True,
		'tools.staticdir.root': base,
		'tools.staticdir.dir': 'test/static',
	},
}

def setupapp():
	if env.production:
		cherrypy.config.update({'environment' : 'production'})
	else:
		app_conf['/_dev'] = {
			'request.dispatch': dev,
		}
	cherrypy.config.update({
		'server.socket_port': env.airportlocker_port,
		'server.thread_pool' : env.threads,
		'log.screen' : True,
		'autoreload_on': True,
	})

	cherrypy.tree.mount(None, config=app_conf)

def run_airportlocker():
	setupapp()
	cherrypy.server.quickstart()
	cherrypy.engine.start()

if __name__ == "__main__":
	run_airportlocker()

