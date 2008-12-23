from __future__ import with_statement
import os
import mimetypes
import uuid
import simplejson
import fab
import cherrypy

from airportlocker.control.base import Resource, HtmlResource, post
from ottoman.envelopes import success, failure

from eggmonster import env


class BasicUpload(HtmlResource):
	template = fab.template('base.tmpl')
	body = fab.template('basicform.tmpl')
	def GET(self, page, *args, **kw):
		page.args = kw

class ListResources(Resource):
	def GET(self, page):
		page.message = 'listing...'
		return simplejson.dumps(self.db.all)

class ViewResource(Resource):
	def GET(self, page, id):
		results = self.db.view('by_id', id)
		if results:
			print results
			return simplejson.dumps(results)
		raise cherrypy.HTTPError(404)

class ReadResource(Resource):
	def GET(self, page, *args, **kw):
		if not args:
			raise cherrypy.HTTPError(404)
		path = '/'.join(args)
		file_path = self.find_file(path)
		if file_path:
			return self.return_file(file_path)
		raise cherrypy.HTTPError(404)

	def find_file(self, path):
		filepath = os.path.join(env.static_files, path)
		if os.path.exists(filepath):
			return path
		for doc in self.db:
			doc = doc[1]
			if '_id' in doc and path == doc['_id']:
				if '_filename' in doc:
					return os.path.join(env.static_files, doc['_filename']) 
		return None

	def return_file(self, path):
		cherrypy.response.headers.update({
			'Content-Size': os.path.getsize(path),
			'Content-Type': mimetypes.guess_type(path),
		})
		with open(path, 'r') as fh:
			for line in fh:
				yield line

class CreateResource(Resource):
	def save_file(self, fs):
		path = os.path.join(env.static_files, fs.filename)
		newfile = open(path, 'w+')
		for chunk in fs.file:
			newfile.write(chunk)
		newfile.close()
		return path

	@post
	def POST(self, page, fields):
		if '_new' in fields and '_lockerfile' in fields:
			meta = dict([
				(k, fields.getvalue(k)) for k in fields.keys()
				if not k.startswith('_')
			])
			meta['_id'] = str(uuid.uuid4())
			meta['_filename'] = self.save_file(fields['_lockerfile'])
			meta['_mime'] = fields['_lockerfile'].type
			if self.db.new(meta):
				return success(meta)
			return failure('Error saving to ottoman')
		return failure('A "_new" and "_locker_file" are required to create a new document.')

class DeleteResource(Resource):
	def DELETE(self, page, id):
		meta = self.db[id]
		self.db.delete(id)
		return success({'deleted': meta})
		
