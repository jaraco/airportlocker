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
		log.info("Migrating %s records", source.coll.count())
		if not self.__validate(source):
			log.info("validation failed; no migration attempted")
			return
		watch = Stopwatch()
		for doc in self.__new_docs(source):
			filename = self.__full_path(doc)
			content_type = doc['_mime']
			meta = dict(
				(k,v) for k,v in doc.items()
				if not k.startswith('_') and k != 'name'
			)
			url = urlparse.urljoin(self.base, doc['_id'])
			stream = urllib2.urlopen(url)
			self._save(stream, filename, content_type, meta)
			log.info("Migrated %s", filename)
		log.info("Migration completed in %s", watch.split())

	def __full_path(self, doc):
		return posixpath.join(doc.get('_prefix', ''), doc['_filename'])

	def __new_docs(self, source):
		return (
			doc for doc in source.coll.find()
			if not self.exists(self.__full_path(doc))
		)

	def __validate(self, source):
		"""
		Validate each of the records in the database (in advance)
		"""
		valid = True
		watch = Stopwatch()
		for doc in self.__new_docs():
			if not '_mime' in doc:
				log.info("%s: no content type", doc['_id'])
				valid = False
			try:
				url = urlparse.urljoin(self.base, doc['_id'])
				req = MethodRequest(url, method='HEAD')
				urllib2.urlopen(req)
			except Exception:
				log.info("error retrieving %s", url)
				valid = False
		log.info("Validation completed in %s", watch.split())
		return valid

# copied from jaraco.net
class MethodRequest(urllib2.Request):
	def __init__(self, *args, **kwargs):
		"""
		Construct a MethodRequest. Usage is the same as for
		`urllib2.Request` except it also takes an optional `method`
		keyword argument. If supplied, `method` will be used instead of
		the default.
		"""
		if 'method' in kwargs:
			self.method = kwargs.pop('method')
		return urllib2.Request.__init__(self, *args, **kwargs)

	def get_method(self):
		return getattr(self, 'method', urllib2.Request.get_method(self))
