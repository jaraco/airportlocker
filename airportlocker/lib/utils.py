import cherrypy

def get_fields():
	if 'Content-Length' in cherrypy.request.headers:
		lchead = dict([(k.lower(), v) for k, v in cherrypy.request.headers.iteritems()])
		data = cgi.FieldStorage(fp=cherrypy.request.rfile,
								headers=lchead,
								environ={'REQUEST_METHOD': 'POST'},
								keep_blank_values=True)
		return data
	return None
	
