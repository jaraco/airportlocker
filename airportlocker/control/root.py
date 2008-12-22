import etc.startup
import cherrypy
from fab.cp_tools import FabDispatcher
from control.hello import HelloPage

from airportlocker.control.urls import get_dispatcher

routes = get_dispatcher()


app_conf = {
	'/' : {
        'request.dispatch': mapper,
        'request.process_request_body': False,
	}
}

if __name__ == "__main__":
	cherrypy.quickstart(None, '/', config=app_conf)

