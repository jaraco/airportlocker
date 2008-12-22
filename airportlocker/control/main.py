import fab
import cherrypy
import simplejson

from airportlocker.control.base import Resource, post
from ottoman.envelopes import success, failure

class ListResources(Resource):
	template = fab.template('list.tmpl')
	def GET(self, page):
		page.mesage = 'listing...'
		page.listing = [d for d in self.db]

class CreateResource(Resource):
	def save_file(self, fs):
		savedir = 'files'
		if not os.path.exists(savedir) or not os.path.isdir(savedir):
			os.mkdir(savedir)
		path = os.path.join(savedir, fs.filename)
		newfile = open(path, 'w+')
		for chunk in fs.file:
			newfile.write(chunk)
		newfile.close()

	@post
	def POST(self, page, fields):
		if '_new' in fields and '_rmfile' in fields:
			meta = dict([(k, fields.getvalue(k)) for k in fields.keys() if not k.startswith('_')])
			meta['_id'] = str(uuid.uuid4())
			self.save_file(fields['_rmfile'])
			if self.db.new(meta):
				return success(meta)
			return failure('Error saving to ottoman')
		return failure('A "_new" and "_locker_file" are required to create a new document.')
