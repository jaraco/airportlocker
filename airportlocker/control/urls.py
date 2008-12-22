from fab.cp_tools import FabDispatcher

from airportlocker.control.main import ListResources, CreateResource
from airportlocker.control.main import BasicUpload


api = FabDispatcher()
api.add_route('index', '', ListResources(), method='GET')
api.add_route('create', '', CreateResource(), method='POST')

dev = FabDispatcher()
dev.add_route('index', '', BasicUpload(), method='GET')




