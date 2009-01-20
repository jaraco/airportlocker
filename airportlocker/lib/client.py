import os
import posixpath
import httplib2
import urlparse

pjoin = posixpath.join

class AirportLockerClient(object):

	def __init__(self, url, h=None):
		self.base = url
		self.h = h or httplib2.Http('.ap_cache')
		self._api = {
			'create': '',
			'update': '/edit',
			'read': '/static',
			'view': '/edit',
			'delete': '/edit',
		}

	def api(self, action, tail=None):
		result = urlparse.urljoin(self.base, pjoin(self._api[action], tail))
		return result

	def create(self, fn, fields=None):
		fields = fields or {}
		fields.update({'_new': 'True'})
		data = MultiPart(fn, fields)
		res, c = self.h.request(self.api('create'),
								method='POST',
								body=data.body,
								headers=data.headers)
		response = simplejson.loads(c)
		return response

	def update(self, id, fn, fields=None):
		fields = fields or {}
		fields.update({'my_extra_data': 'foo'})
		data = MultiPart(fn, fields)
		res, c = self.h.request(self.api('update', id),
								method='PUT',
								body=data.body,
								headers=data.headers)
		response = simplejson.loads(c)
		return response
	
	def view(self, id):
		res, c = self.h.request(self.api('view', id))
		return simplejson.loads(c)

	def read(self, path):
		res, c = self.h.request(self.api('read', path))
		return c

	def delete(self, id):
		res, c = self.h.request(self.api('delete', id), method='DELETE')
		response = simplejson.loads(c)
		return response
			
	
