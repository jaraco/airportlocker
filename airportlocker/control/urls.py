from fab.cp_tools import FabDispatcher

from airportlocker.control.main import BasicUpload
from airportlocker.control.main import CachedResource
from airportlocker.control.main import CreateResource
from airportlocker.control.main import CreateOrReplaceResource
from airportlocker.control.main import DeleteResource
from airportlocker.control.main import ListResources
from airportlocker.control.main import ListSignedResources
from airportlocker.control.main import ReadResource
from airportlocker.control.main import GetInternalResource
from airportlocker.control.main import GetPrivateResource
from airportlocker.control.main import GetPublicResource
from airportlocker.control.main import UpdateResource
from airportlocker.control.main import ViewResource
from airportlocker.control.main import ZencoderResource


api = FabDispatcher()
api.add_route('signed', 'signed/*', ListSignedResources(), method='GET')
api.add_route('cached', 'cached/*', CachedResource(), method='GET')
api.add_route('zencoder', '_zencoder', ZencoderResource(), method='POST')

api.add_route('read', 'static/*', ReadResource(), method='GET')
api.add_route('head', 'static/*', ReadResource(), method='HEAD')
api.add_route('view', 'view/:id', ViewResource(), method='GET')
api.add_route('internal', 'internal/:md5/:file', GetInternalResource(),
    method='GET')
api.add_route('private', 'private/:md5/:file', GetPrivateResource(),
    method='GET')
api.add_route('public', 'public/:md5/:file', GetPublicResource(), method='GET')
api.add_route('view-options', 'view/:id', ViewResource(), method='OPTIONS')
# overloaded POST for browsers
# TODO: make _method tool
api.add_route('post_delete', 'edit/:id', DeleteResource(), method='POST')
api.add_route('post_update', 'edit/:id', UpdateResource(), method='PUT')
api.add_route('delete', 'edit/:id', DeleteResource(), method='DELETE')
api.add_route('index', '', ListResources(), method='GET')
api.add_route('create', '', CreateResource(), method='POST')
api.add_route('options', '', CreateResource(), method='OPTIONS')
api.add_route('create_or_replace', 'post', CreateOrReplaceResource(),
    method='POST')
api.add_route('options_cor', 'post', CreateOrReplaceResource(),
    method='OPTIONS')

dev = FabDispatcher()
dev.add_route('index', '_dev', BasicUpload(), method='GET')
