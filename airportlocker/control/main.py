from __future__ import with_statement
import os
import glob
import mimetypes
import uuid
import simplejson
import fab
import cherrypy

from airportlocker.control.base import Resource, HtmlResource, post
from airportlocker.lib.resource import ResourceMixin
from ottoman.lib.envelopes import success, failure

from eggmonster import env


class BasicUpload(HtmlResource):
	template = fab.template('base.tmpl')
	body = fab.template('basicform.tmpl')
	def GET(self, page, *args, **kw):
		page.args = kw

class ListResources(Resource):
	def GET(self, page):
		all = []
		for id in list(self.db):
			row = self.db.get_by_id(id, json=False)
			row = simplejson.loads(row)
			row['url'] = '/static/%s' % row['_id']
			all.append(row)
		return simplejson.dumps(all, indent=2)

class ViewResource(Resource):
	def GET(self, page, id):
		results = self.db.get_by_id(id) 
		if results:
			return simplejson.dumps(results)
		raise cherrypy.HTTPError(404)

class ReadResource(Resource):
	def GET(self, page, *args, **kw):
		if not args:
			raise cherrypy.HTTPError(404)
		path = '/'.join(args)
		return self.return_file(path)

	def get_resource(self, key):
		resource = None
		ct = 'application/octet-stream'
		try:
			resource = self.fs.get_by_id(key)
			ct, enc = mimetypes.guess_type(key)
		except KeyError:
			pass
		if not resource:
			try:
				doc = self.db.get_by_id(key)
				resource = self.fs.get_by_id(doc['name'])
				ct = doc['_mime']
			except KeyError:
				pass
		return resource, ct

	def return_file(self, path):
		resource, ct = self.get_resource(path)
		if not resource:
			raise cherrypy.HTTPError(404)
		cherrypy.response.headers.update({
			'Content-Type': ct or 'text/plain',
		})
		return resource

class CreateResource(Resource, ResourceMixin):
	'''This saves the file and makes sure the filename is as close as
	possible to the original while stilling being unique.'''
	@post
	def POST(self, page, fields):
		if '_new' in fields and '_lockerfile' in fields:
			meta = dict([
				(k, fields.getvalue(k)) for k in fields.keys()
				if not k.startswith('_')
			])
			meta['_id'] = str(uuid.uuid4())
			if 'name' in fields:
				fn = fields['name'].value
			else:
				fn = fields['_lockerfile'].filename
			meta['_filename'] = self.fs.create_doc(fn, fields['_lockerfile'])
			meta['name'] = meta['_filename']
			meta['_mime'] = fields['_lockerfile'].type
			print meta
			result = self.db.create_doc(meta['_id'], simplejson.dumps(meta))
			return success(result)
		return failure('A "_new" and "_lockerfile" are required to create a new document.')

class DeleteResource(Resource):
	def DELETE(self, page, id):
		meta = {}
		try:
			meta = self.db.get_by_id(id)
			self.fs.delete_by_id(meta['name'])
			self.db.delete_by_id(id)
		except KeyError, e:
			print e
		return success({'deleted': meta})
		

