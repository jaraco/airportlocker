import cherrypy

from airportlocker.control.main import BasicUpload
from airportlocker.control.main import CachedResource
from airportlocker.control.main import CreateOrReplaceResource
from airportlocker.control.main import EditResource
from airportlocker.control.main import ListSignedResources
from airportlocker.control.main import ReadResource
from airportlocker.control.main import RootResources
from airportlocker.control.main import GetInternalResource
from airportlocker.control.main import GetPrivateResource
from airportlocker.control.main import GetPublicResource
from airportlocker.control.main import ViewResource
from airportlocker.control.main import ZencoderResource

api = cherrypy.dispatch.RoutesDispatcher()

api.connect('signed', '/signed', ListSignedResources())
api.connect('cached', '/cached', CachedResource())
api.connect('zencoder', '/_zencoder', ZencoderResource())

api.connect('read', '/static/{path:.*}', ReadResource())
api.connect('view', '/view/:id', ViewResource())
api.connect('internal', '/internal/:md5/:file', GetInternalResource())
api.connect('private', '/private/:md5/:file', GetPrivateResource())
api.connect('public', '/public/:md5/:file', GetPublicResource())
api.connect('view-options', '/view/:id', ViewResource())
api.connect('edit', '/edit/:id', EditResource())
api.connect('index', '/', RootResources())
api.connect('post', '/post', CreateOrReplaceResource())

dev = cherrypy.dispatch.RoutesDispatcher()
dev.connect('dev', '/_dev', BasicUpload())
