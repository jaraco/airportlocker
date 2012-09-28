from __future__ import with_statement
import uuid

import fab
import cherrypy

from airportlocker import json
from airportlocker.control.base import Resource, HtmlResource, post
from airportlocker.lib.resource import ResourceMixin

def success(value):
	return json.dumps({'status': 'success', 'value': value})

def failure(message):
	return json.dumps({'status': 'failure', 'reason': message})

class BasicUpload(HtmlResource):
	template = fab.template('base.tmpl')
	body = fab.template('basicform.tmpl')
	def GET(self, page, *args, **kw):
		page.args = kw


class ListResources(Resource):
	def GET(self, page, q=None, **kw):
		if q or kw:
			cherrypy.response.headers['Cache-Control'] = 'no-cache'
			if q == '__all':
				res = self._list()
			else:
				res = self._query(**kw)
			return json.dumps(res)
		# need a query
		raise cherrypy.HTTPError(404)

	def _list(self):
		def add_url(row):
			row['url'] = '/static/%(_id)s' % row
			return row
		return map(add_url, self.db.find())

	def _query(self, **kw):
		"""
		Return all records that match the query.
		"""
		return list(self.db.find(kw))

class ViewResource(Resource):
	def GET(self, page, id):
		results = self.db.find_one(dict(_id=id))
		if not results:
			raise cherrypy.HTTPError(404)
		return json.dumps(results)

class ReadResource(Resource, ResourceMixin):
	def GET(self, page, *args, **kw):
		if not args:
			raise cherrypy.HTTPError(404)
		path = '/'.join(args)
		cherrypy.response.headers['Connection'] = 'close'
		return self.return_file(path)

	def HEAD(self, page, *args, **kw):
		path = '/'.join(args)
		cherrypy.response.headers['Connection'] = 'close'
		return self.head_file(path)

class CreateResource(Resource, ResourceMixin):
	'''
	Save the file and make sure the filename is as close as possible to the
	original while still being unique.
	'''
	cases = [
		'_prefix',
	]

	@post
	def POST(self, page, fields):
		'''Uses the ResourceMixin to save the file'''
		fields_valid = '_new' in fields and '_lockerfile' in fields
		if not fields_valid:
			return failure('A "_new" and "_lockerfile" are required to create '
						   'a new document.')

		# clean up the meta data
		meta = dict([
			(k, fields.getvalue(k)) for k in fields.keys()
			if not k.startswith('_') or k in self.cases
		])
		# gen an id
		meta['_id'] = str(uuid.uuid4())

		# give it a name
		if 'name' in fields:
			fn = fields['name'].value
		else:
			fn = fields['_lockerfile'].filename

		# save the file and grab its name
		meta['_filename'] = self.save_file(fields['_lockerfile'], fn, prefix=meta.get('_prefix'))
		meta['name'] = meta['_filename']
		meta['_mime'] = fields['_lockerfile'].type
		inserted_id = self.db.insert(meta)
		return success(inserted_id)

class UpdateResource(Resource, ResourceMixin):

	def get_doc(self, key):
		return self.db.find_one(dict(_id=key))

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
		spec = dict(_id=id)
		self.db.update(spec, meta)
		new_doc = self.get_doc(id)
		if have_file:
			self.update_file(new_doc['name'], fields['_lockerfile'].file)
		return success({'updated': json.dumps(new_doc)})

class DeleteResource(Resource, ResourceMixin):
	def DELETE(self, page, id):
		meta = self.db.find_one(dict(_id=id)) or {}
		if meta:
			self.remove_file(meta['name'])
			self.db.remove(id)
		return success({'deleted': meta})

