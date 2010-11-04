import os
import posixpath
import httplib2
import urlparse

from airportlocker.lib.utils import MultiPart
from airportlocker import json
pjoin = posixpath.join

class AirportLockerClient(object):

	def __init__(self, url, h=None):
		self.base = url
		self.h = h or httplib2.Http('.ap_cache')
		self._api = {
			'query': '',
			'create': '',
			'update': '/edit',
			'read': '/static',
			'view': '/view',
			'delete': '/edit',
		}

	def api(self, action, tail=None, prefix=None, use_host=True):
		tail = tail or ''
		prefix =  prefix or ''
		base = self.base
		if not use_host:
			base = ''
		result = urlparse.urljoin(base, pjoin(self._api[action], prefix, tail))
		return result

	def create(self, fn, fields=None):
		fields = fields or {}
		fields.update({'_new': 'True'})
		data = MultiPart(fn, fields)
		res, c = self.h.request(self.api('create'),
								method='POST',
								body=data.body,
								headers=data.headers)
		if res.status < 300:
			response = json.loads(c)
		else:
			res['content'] = c
			return res
		return response

	def update(self, id, fn, fields=None):
		fields = fields or {}
		data = MultiPart(fn, fields)
		res, c = self.h.request(self.api('update', id),
								method='PUT',
								body=data.body,
								headers=data.headers)
		response = json.loads(c)
		return response
	
	def view(self, id):
		res, c = self.h.request(self.api('view', id))
		return json.loads(c)

	def read(self, path, prefix=''):
		res, c = self.h.request(self.api('read', path))
		return c

	def delete(self, id):
		res, c = self.h.request(self.api('delete', id), method='DELETE')
		response = json.loads(c)
		return response

	def exists(self, id, prefix=None):
		prefix = prefix or ''
		res, c = self.h.request(self.api('read', id, prefix=prefix), method='HEAD')
		return res['status'].startswith('20')

	def query(self, qs):
		qs = '?q=%s' % qs
		res, c = self.h.request(self.api('query', qs))
		return json.loads(c)
	
