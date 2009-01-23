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

class ReadResource(Resource, ResourceMixin):
	def GET(self, page, *args, **kw):
		if not args:
			raise cherrypy.HTTPError(404)
		path = '/'.join(args)
		return self.return_file(path)

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
			meta['_filename'] = self.save_file(fields['_lockerfile'], fn)
			meta['name'] = meta['_filename']
			meta['_mime'] = fields['_lockerfile'].type
			result = self.db.create_doc(meta['_id'], simplejson.dumps(meta))
			return success(result)
		return failure('A "_new" and "_lockerfile" are required to create a new document.')

class UpdateResource(Resource, ResourceMixin):

	def get_doc(self, key):
		try:
			return self.db.get_by_id(key)
		except KeyError:
			return None
	
	@post
	def PUT(self, page, fields, id):
		cur_doc = self.get_doc(id)
		if not cur_doc:
			raise cherrypy.HTTPNotFound()
		have_file = bool('_lockerfile' in fields)
		meta = dict([
			(k, fields.getvalue(k)) for k in fields.keys()
			if not k.startswith('_')
		])
		meta['_id'] = cur_doc['_id']
		meta['_filename'] = cur_doc['_filename']
		meta['name'] = cur_doc['name']
		if have_file:
			meta['_mime'] = fields['_lockerfile'].type or cur_doc['_mime']
		self.db.update_by_id(id, simplejson.dumps(meta))
		new_doc = self.get_doc(id)
		if have_file:
			self.update_file(new_doc['name'], fields['_lockerfile'].file)
		return success({'updated': simplejson.dumps(new_doc)})

class DeleteResource(Resource, ResourceMixin):
	def DELETE(self, page, id):
		meta = {}
		try:
			meta = self.db.get_by_id(id)
			self.remove_file(meta['name'])
			self.db.delete_by_id(id)
		except KeyError, e:
			# if it's missing it's deleted
			pass
		return success({'deleted': meta})
		

