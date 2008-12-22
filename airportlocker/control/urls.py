from fab.cp_tools import FabDispatcher

from airportlocker.control.main import api

def get_dispatcher():
	r = FabDispatcher()
	for name, route, cls, method in api:
		r.add_rout(name, route, cls(), method=method)
	return r
