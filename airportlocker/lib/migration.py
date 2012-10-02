"""
Routines to migrate from previous versions of airportlocker.
"""
from __future__ import print_function, unicode_literals, absolute_import

import logging
import posixpath
import urllib2
import urlparse

from jaraco.util.timing import Stopwatch

import airportlocker.lib.filesystem

log = logging.getLogger(__name__)

class FSMigration(object):
	def migrate(self, retrieve_base):
		"""
		Migrate data from a previous filesystem-backed instance.
		"""
		self.base = retrieve_base
		# first validate the source
		source = airportlocker.lib.filesystem.FileStorage()
		print("Migrating", source.coll.count(), "records")
		if not self.__validate(source):
			print("validation failed; no migration attempted")
			return
		watch = Stopwatch()
		for doc in source.coll.find():
			filename = posixpath.join(doc.get('_prefix', ''),
				doc['_filename'])
			if self.exists(filename):
				continue
			content_type = doc['_mime']
			meta = dict(
				(k,v) for k,v in doc.items()
				if not k.startswith('_') and k != 'name'
			)
			url = urlparse.urljoin(self.base, doc['_id'])
			stream = urllib2.urlopen(url)
			self._save(stream, filename, content_type, meta)
			print("Migrated", filename)
		print("Migration completed in", watch.split())

	def __validate(self, source):
		"""
		Validate each of the records in the database (in advance)
		"""
		valid = True
		for doc in source.coll.find():
			if not '_mime' in doc:
				print("no content type")
				valid = False
			try:
				url = urlparse.urljoin(self.base, doc['_id'])
				urllib2.urlopen(url)
			except Exception:
				print("error retrieving", url)
				valid = False
		return valid
