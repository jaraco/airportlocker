import cgi
import fab
import cherrypy

from eggmonster import env

class Resource(fab.FabPage):

	@property
	def db(self):
		pool = fab.pool('db')
		db = pool.get()
		# replace with env call
		docs = db.docset(env.docset)
		return docs

	def is_json(self):
		json_types = ['application/json', 'text/json', 'text/plain']
		print cherrypy.response.headers
		return cherrypy.response.headers['Content-Type'] in json_types
	
	def control(self, page, *args, **kw):
		m = cherrypy.request.method.upper()
		if kw.get('_method'):
			m = kw['_method'].upper()
			del kw['_method']
		if not hasattr(self, m):
			raise cherrypy.HTTPError(405)

		cherrypy.response.headers['Content-Type'] = 'text/plain' # 'application/json'

		# these are top level actions so we remove them from the kw args
		jsonp_cb = kw.get('jsonp_callback', None)
		if jsonp_cb:
			del kw['jsonp_callback']

		redirect_url = kw.get('_redirect', None)
		if redirect_url:
			del kw['_redirect']

		# get the actual result
		source = getattr(self, m)(page, *args, **kw)

		if redirect_url:
			raise cherrypy.HTTPRedirect(redirect_url)
		
		if jsonp_cb and self.is_json():
			cherrypy.response.headers['Content-Type'] = 'text/javascript'
			return '%s(%s);' % (jsonp_cb, source)
		return source


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
		
