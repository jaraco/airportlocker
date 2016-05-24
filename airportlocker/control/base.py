import datetime

import cherrypy
from cherrypy.lib import httputil


class MethodHandler(object):
    """
    Subclasses must implement the actual HTTP methods (GET, POST, etc) that
    are allowed to operate on the resource.  They should be implemented as
    Python methods.
    """

    # Stolen from Gryphon.control.admin.resources.
    # TODO: put this somewhere, maybe fab, where it can be shared.

    @cherrypy.expose
    def index(self, *args, **params):
        method = self.get_method()
        handler = self.get_handler(method)
        if self.check_handler(method=method, handler=handler):
            print("Handler is", handler, args, params)
            return handler(*args, **params)

    def get_handler(self, method):
        return getattr(self, method, None)

    def get_method(self):
        return cherrypy.request.method.upper()

    def check_handler(self, raise_exception=True, *args, **params):
        method = params.get('method', self.get_method())
        handler = params.get('handler', self.get_handler(method))
        if handler:
            return True
        elif not raise_exception:
            return False
        else:
            error_message = (
                "This endpoint (handled by the %(class_name)s class) "
                "does not support the %(method)s method" % {
                    'method': method,
                    'class_name': self.__class__.__name__
                }
            )
            raise cherrypy.HTTPError(405, error_message)


class Resource(MethodHandler):

    def is_json(self):
        json_types = ['application/json', 'text/json', 'text/plain']
        return cherrypy.response.headers['Content-Type'] in json_types

    def __call__(self, *args, **kw):
        print("in resource", args, kw)
        cherrypy.response.headers['Content-Type'] = 'text/plain' # 'application/json'

        # these are top level actions so we remove them from the kw args
        jsonp_cb = kw.pop('jsonp_callback', None)
        redirect_url = kw.pop('_redirect', None)

        # remove underscore, which is sometimes included to suppress caching
        kw.pop('_', None)

        resp = self.index(*args, **kw)

        if redirect_url:
            raise cherrypy.HTTPRedirect(redirect_url)

        if jsonp_cb and self.is_json():
            # wrap the response a callback for JSONP.
            return '%s(%s);' % (jsonp_cb, resp)

        return resp

    def OPTIONS(self):
        """
        Expose the Access-Control-Allow-Origin header
        when an ajax request asks for it before a POST
        """
        cherrypy.response.status = 201
        return

    def _format_datetime(self, dt):
        epoch = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
        return httputil.HTTPDate(epoch)
