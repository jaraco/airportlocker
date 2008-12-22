from fab.cp_tools import FabDispatcher

from airportlocker.control.main import ListResources, CreateResource

def get_dispatcher():
	r = FabDispatcher()
	r.add_route('index', '', ListResources(), method='GET')
	r.add_route('create', '', CreateResource(), method='POST'),
	return r
