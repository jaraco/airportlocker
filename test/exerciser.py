import os
import shutil
import urlparse

import httplib2
import simplejson
import py.test

from optparse import OptionParser
from pprint import pprint

from airportlocker.lib.utils import MultiPart

def create_sample_file():
	sample_file = os.path.join(os.path.abspath(os.getcwd()), 'sample.txt')
	fh = open(sample_file, 'w+')
	for i in range(0, 10):
		fh.write('%s) hello world\n' % i)
	fh.close()

class AirportLockerClient(object):
	
	def __init__(self, base):
		self.h = httplib2.Http()
		self.base = base

	def api(self, tail=None):
		return urlparse.urljoin(self.base, tail)

	def create(self, fn, fields=None):
		fields = fields or {}
		fields.update({'_new': 'True'})
		data = MultiPart(fn, fields)
		res, c = self.h.request(self.api(),
								method='POST',
								body=data.body,
								headers=data.headers)
		try:
			response = simplejson.loads(c)
		except ValueError:
			pprint(res)
			print c
			raise
		return response

	def view(self, id):
		res, c = self.h.request(self.api('/view/%s' % id))
		return simplejson.loads(c)

	def read(self, path):
		res, c = self.h.request(self.api('/static/%s' % path))
		return c

	def delete(self, id):
		res, c = self.h.request(self.api('/edit/%s' % id), method='DELETE')
		response = simplejson.loads(c)
		return response


if __name__=='__main__':
	usage = 'usage: %prog [options] url'
	parser = OptionParser(usage)
	(options, args) = parser.parse_args()
	if len(args) < 1:
		parser.error('Need an airportlocker url')
	url = args[0]
	excerciser = AirportLockerClient(url)
	create_sample_file()
	sample_fn = 'sample.txt'
	sample = excerciser.create(sample_fn, {'yeah' : 'this field'})
# 	doc = excerciser.view(sample['value'])
# 	print excerciser.read(doc['name'])
# 	print 'Deleted:'
 	deleted = excerciser.delete(sample['value'])
# 	pprint(deleted)
	
	
