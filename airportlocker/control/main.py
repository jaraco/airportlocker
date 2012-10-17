from __future__ import with_statement

import fab
import cherrypy

import airportlocker
from airportlocker import json
from airportlocker.control.base import Resource, HtmlResource, post
from airportlocker.lib.storage import NotFoundError

def success(value):
	return json.dumps({'status': 'success', 'value': value})

def failure(message):
	return json.dumps({'status': 'failure', 'reason': message})

def items(field_storage):
	"""
	Like dict.items, but for cgi.FieldStorage
	"""
	for key in field_storage.keys():
		yield key, field_storage.getvalue(key)

class BasicUpload(HtmlResource):
	template = fab.template('base.tmpl')
	body = fab.template('basicform.tmpl')
	def GET(self, page, *args, **kw):
		cherrypy.response.headers['Content-Type'] = 'application/xhtml+xml'
		page.args = kw


class ListResources(Resource, airportlocker.storage_class):
	def GET(self, page, **kw):
		cherrypy.response.headers['Cache-Control'] = 'no-cache'
		# traditionally, q must be __all to query all. Now that's the default
		#  behavior if no kw is passed... but support it for compatibility.
		kw.pop('q', None)
		if kw:
			res = self._query(**kw)
		else:
			res = self._list()
		return json.dumps(res)

	def _list(self):
		def add_url(row):
			row['url'] = '/static/%(_id)s' % row
			return row
		return map(add_url, self.find())

	def _query(self, **kw):
		"""
		Return all records that match the query.
		"""
		return list(self.find(kw))

class ViewResource(Resource, airportlocker.storage_class):
	def GET(self, page, id):
		results = self.find_one(self.by_id(id))
		if not results:
			raise cherrypy.NotFound()
		return json.dumps(results)

class ReadResource(Resource, airportlocker.storage_class):
	def GET(self, page, *args, **kw):
		if not args:
			raise cherrypy.NotFound()
		path = '/'.join(args)
		cherrypy.response.headers['Connection'] = 'close'
		return self.return_file(path)

	def HEAD(self, page, *args, **kw):
		path = '/'.join(args)
		cherrypy.response.headers['Connection'] = 'close'
		return self.head_file(path)

	def return_file(self, path):
		try:
			resource, ct = self.get_resource(path)
		except NotFoundError:
			raise cherrypy.NotFound()
		cherrypy.response.headers.update({
			'Content-Type': ct or 'text/plain',
		})
		return resource

	def head_file(self, path):
		try:
			resource, ct = self.get_resource(path)
		except NotFoundError:
			raise cherrypy.NotFound()
		size = sum([len(l) for l in resource])
		cherrypy.response.headers.update({
			'Content-Type': ct or 'text/plain',
			'Content-Length': size,
		})
		return

class CreateResource(Resource, airportlocker.storage_class):
	'''
	Save the file and make sure the filename is as close as possible to the
	original while still being unique.
	'''
	cases = [
		'_prefix',
	]
	"A list of all metadata keys that begin with _"

	@post
	def POST(self, page, fields):
		'''Save the file to storage'''
		fields_valid = '_new' in fields and '_lockerfile' in fields
		if not fields_valid:
			return failure('A "_new" and "_lockerfile" are required to '
				'create a new document.')

		# clean up the meta data
		meta = dict(
			(k, v) for k, v in items(fields)
			if not k.startswith('_') or k in self.cases
		)

		# use override name field if supplied, else use source filename
		name = (fields['name'].value
			if 'name' in fields else fields['_lockerfile'].filename)

		return success(self.save(fields['_lockerfile'], name, meta))

class UpdateResource(Resource, airportlocker.storage_class):

	cases = [
		'_prefix',
	]
	"A list of all metadata keys that begin with _"

	@post
	def PUT(self, page, fields, id):
		if not self.exists(id):
			raise cherrypy.NotFound()

		cp_file = fields.get('_lockerfile', None)

		# clean up the meta data
		meta = dict(
			(k, v) for k, v in items(fields)
			if not k.startswith('_') or k in self.cases
		)

		try:
			new_doc = self.update(id, meta, cp_file)
		except NotFoundError:
			raise cherrypy.NotFound()

		return success({'updated': json.dumps(new_doc)})

class DeleteResource(Resource, airportlocker.storage_class):
	def DELETE(self, page, id):
		return success({'deleted': self.delete(id)})
