import cgi
import fab
import cherrypy

class Resource(fab.FabPage):

	def is_json(self):
		json_types = ['application/json', 'text/json', 'text/plain']
		return cherrypy.response.headers['Content-Type'] in json_types

	def control(self, page, *args, **kw):
		method_name = kw.pop('_method', None) or cherrypy.request.method
		method = getattr(self, method_name.upper(), None)
		if not method:
			raise cherrypy.HTTPError(405)

		cherrypy.response.headers['Content-Type'] = 'text/plain' # 'application/json'

		# these are top level actions so we remove them from the kw args
		jsonp_cb = kw.pop('jsonp_callback', None)
		redirect_url = kw.pop('_redirect', None)

		# remove underscore, which is sometimes included to suppress caching
		kw.pop('_', None)

		# invoke the method and get the response
		resp = method(page, *args, **kw)

		if redirect_url:
			raise cherrypy.HTTPRedirect(redirect_url)

		if jsonp_cb and self.is_json():
			# wrap the response a callback for JSONP.
			cherrypy.response.headers['Content-Type'] = 'text/javascript'
			return '%s(%s);' % (jsonp_cb, resp)

		return resp

	def OPTIONS(self, page):
		""" We need an options method so we can expose the
		Access-Control-Allow-Origin header when an ajax request
		asks for it before a POST """
		cherrypy.response.status = 201
		return


class HtmlResource(Resource):
	template = fab.template('base.tmpl')

def get_fields():
	headers = cherrypy.request.headers
	if 'Content-Length' in headers:
		lchead = dict([(k.lower(), v) for k, v in headers.iteritems()])
		data = cgi.FieldStorage(fp=cherrypy.request.rfile,
								headers=lchead,
								environ={'REQUEST_METHOD': 'POST'},
								keep_blank_values=True)
		return data
	return None

def post(fn):
	def process_post(cls, page, *args, **kw):
		fields = get_fields()
		if fields:
			return fn(cls, page, fields, *args, **kw)
		return fn(cls, page, *args, **kw)
	return process_post
