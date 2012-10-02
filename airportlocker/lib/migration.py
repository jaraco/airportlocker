"""
Routines to migrate from previous versions of airportlocker.
"""
from __future__ import print_function, unicode_literals, absolute_import

import logging
import posixpath
import urllib2

import airportlocker.lib.filesystem

log = logging.getLogger(__name__)

class FSMigration(object):
	def migrate(self):
		return self.__from_filesystem()

	def __from_filesystem(self):
		"""
		Migrate data from a previous filesystem-backed instance.
		"""
		# first validate the source
		source = airportlocker.lib.filesystem.FileStorage()
		source.url = 'http://vairprt:8090/static/'
		if not self.__validate(source):
			print("validation failed; no migration attempted")
			return
		for doc in source.coll.find():
			filename = posixpath.join(doc.get('_prefix', ''),
				doc['_filename'])
			content_type = doc['_mime']
			meta = dict(
				(k,v) for k,v in doc.items()
				if not k.startswith('_') and k != 'name'
			)
			url = urllib2.urljoin(source.url, doc['_id'])
			stream = urllib2.urlopen(url)
			self._save(stream, filename, content_type, meta)

	def __validate(source):
		"""
		Validate each of the records in the database (in advance)
		"""
		valid = True
		for doc in source.coll.find():
			if not '_mime' in doc:
				print("no content type")
				valid = False
			try:
				url = urllib2.urljoin(source.url, doc['_id'])
				urllib2.urlopen(url)
			except Exception:
				print("error retrieving", url)
				valid = False
		return valid
