import airportlocker.etc.startup

import cherrypy
from fab.cp_tools import FabDispatcher

from airportlocker.control.urls import get_dispatcher

from eggmonster import env

routes = get_dispatcher()


app_conf = {
	'global': {
		'script_name': '/',
	},
	'/' : {
        'request.dispatch': routes,
        'request.process_request_body': False,
	}
}

def setupapp():
	cherrypy.config.update({'server.socket_port': env.airportlocker_port,})
# 	if env.production:
# 		cherrypy.config.update({
# 			'environment' : 'production',
# 			'log.screen' : True,
# 		})
	cherrypy.tree.mount(None, config=app_conf)

def run_airportlocker():
	setupapp()
	cherrypy.server.quickstart()
	cherrypy.engine.start()

if __name__ == "__main__":
	run_airportlocker()

