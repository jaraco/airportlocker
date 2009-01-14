from __future__ import with_statement
import cherrypy
import mimetypes

def get_fields():
	if 'Content-Length' in cherrypy.request.headers:
		lchead = dict([(k.lower(), v) for k, v in cherrypy.request.headers.iteritems()])
		data = cgi.FieldStorage(fp=cherrypy.request.rfile,
								headers=lchead,
								environ={'REQUEST_METHOD': 'POST'},
								keep_blank_values=True)
		return data
	return None
	

# this is primarily used in testing but might be helpful generally

class MultiPart(object):
	boundary = '----------12308129817491874--'
	le = '\r\n'
	cd = 'Content-Disposition: form-data;'
	field_header = ' '.join([cd, 'name="%s";'])
	file_header = ' '.join([cd, 'name="%s"; filename="%s"'])
	lbreak = ''
	
	def __init__(self, fn, fields=None):
		self.fn = fn
		self.fields = fields or {}
		self.filename_key = '_lockerfile'
		self.body = self._get_body()
		self.headers = self._get_headers()

	def _start(self):
		return '--%s' % self.boundary

	def _end(self):
		return '--%s--' % self.boundary


	def _content_type(self):
		return 'Content-Type: %s' % (mimetypes.guess_type(self.fn)[0])

	def _get_headers(self):
		return {
			'Content-Type': 'multipart/form-data; boundary=%s' % self.boundary,
			'Content-Length': str(len(self.body)),
		}

	def _get_body(self):
		body = []
		for k, v in self.fields.items():
			body.append(self._start())
			body.append(self.field_header % k)
			body.append(self.lbreak)
			body.append(v)
		with open(self.fn, 'r') as fh:
			body.append(self._start())
			body.append(self.file_header % (self.filename_key, self.fn))
			body.append(self._content_type())
			body.append(self.lbreak)
			body.append(fh.read())
		body.append(self._end())
		body.append(self.lbreak)
		return self.le.join(body)
