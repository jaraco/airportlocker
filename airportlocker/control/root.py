import airportlocker.etc.startup

import os
import cherrypy
from fab.cp_tools import FabDispatcher

from airportlocker.control.urls import api, dev

from eggmonster import env


app_conf = {
	'global': {
		'script_name': '/',
	},
	'/' : {
        'request.dispatch': api,
        'request.process_request_body': False,
	},
	'/_dev' : {
		'request.dispatch': dev,
	}
}

def setupapp():
	if not os.path.exists(env.static_files) or not os.path.isdir(env.static_files):
		os.mkdir(env.static_files)

	cherrypy.config.update({
		'server.socket_port': env.airportlocker_port,
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

