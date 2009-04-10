from __future__ import with_statement
import os
import glob
import uuid
import simplejson
import fab
import cherrypy

from string import Template

from airportlocker.control.base import Resource, HtmlResource, post
from airportlocker.lib.resource import ResourceMixin
from ottoman.lib.envelopes import success, failure

from eggmonster import env

from pprint import pprint


class BasicUpload(HtmlResource):
	template = fab.template('base.tmpl')
	body = fab.template('basicform.tmpl')
	def GET(self, page, *args, **kw):
		page.args = kw


class ListResources(Resource):
	code_template = Template('''
def filter(i, val):
	if '$key' in i and i['$key'] == val:
		return i
''')
	
	def GET(self, page, q=None, **kw):
		if q or kw:
			cherrypy.response.headers['Cache-Control'] = 'no-cache'
			if q == '__all':
				res = self._list()
			else:
				res = self._query(**kw)
			return simplejson.dumps(res)
		# need a query
		raise cherrypy.HTTPError(404)

	def _list(self):
		all = []
		for id in list(self.db):
			row = self.db.get_by_id(id, json=False)
			row = simplejson.loads(row)
			row['url'] = '/static/%s' % row['_id']
			all.append(row)
		return all

	def _query(self, **kw):
		def fetcher(invalid):
			keys = set(self.db) if invalid is None else invalid.copy()
			for k in keys:
				try:
					yield k, self.db.get_by_id(k)
				except KeyError:
					yield k, None # skip missing keys

		results = {}
		for view, arg in kw.iteritems():
			try:
				self.db.get_view(view)
			except KeyError:
				self.db.save_view(view, self.code_template.substitute({'key': view}))
			results.update(self.db.apply_view(view, (arg,), fetcher))
		return results
		

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
		cherrypy.response.headers['Connection'] = 'close'
		return self.return_file(path)

	def HEAD(self, page, *args, **kw):
		path = '/'.join(args)
		cherrypy.response.headers['Connection'] = 'close'		
		return self.head_file(path)

class CreateResource(Resource, ResourceMixin):
	'''This saves the file and makes sure the filename is as close as
	possible to the original while stilling being unique.'''
	cases = [
		'_prefix',
	]

	@post
	def POST(self, page, fields):
		'''Uses the ResourceMixin to save the file'''
		if '_new' in fields and '_lockerfile' in fields:
			meta = dict([
				(k, fields.getvalue(k)) for k in fields.keys()
				if not k.startswith('_') or k in self.cases
			])
			meta['_id'] = str(uuid.uuid4())
			if 'name' in fields:
				fn = fields['name'].value
			else:
				fn = fields['_lockerfile'].filename
			meta['_filename'] = self.save_file(fields['_lockerfile'], fn, prefix=meta.get('_prefix'))
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
		
