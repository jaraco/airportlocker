import airportlocker.etc.startup

import os
import cherrypy


from airportlocker.control.urls import api, dev

from eggmonster import env

base = os.getcwd()

app_conf = {
	'global': {
		'script_name': '/',
	},
	'/' : {
        'request.dispatch': api,
        'request.process_request_body': False,
	},
	'/_test' : {
		'tools.staticdir.on': True,
		'tools.staticdir.root': base,
		'tools.staticdir.dir': 'test/static',
	},
	'/_dev' : {
		'request.dispatch': dev,
	}
}

def setupapp():
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

