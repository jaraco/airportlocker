import cgi
import fab
import cherrypy


class Resource(fab.FabPage):

	@property
	def db(self):
		pool = fab.pool('db')
		db = pool.get()

		# replace with env call
		docs = db.docset('foo')
		return docs
		
	def control(self, page, *args, **kw):
		m = cherrypy.request.method.upper()
		if not hasattr(self, m):
			raise cherrypy.HTTPError(405)
		return getattr(self, m)(page, *args, **kw)


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
		
