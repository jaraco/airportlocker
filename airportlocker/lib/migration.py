"""
Routines to migrate from previous versions of airportlocker.
"""
from __future__ import print_function, unicode_literals, absolute_import

import logging
import posixpath
import urllib2
import urlparse
import argparse
import importlib
import mimetypes

from jaraco.util.timing import Stopwatch

import airportlocker.lib.filesystem
import airportlocker.config.gridfs

log = logging.getLogger(__name__)

class FSMigration(object):
	def migrate(self, retrieve_base, bad_ids=()):
		"""
		Migrate data from a previous filesystem-backed instance. Skip any
		documents identified by bad_ids.
		"""
		self.base = retrieve_base
		self.bad_ids = set(bad_ids)
		# first validate the source
		source = airportlocker.lib.filesystem.FileStorage()
		docs = self.__new_docs(source)
		log.info("Migrating %s records", len(docs))
		if not self.__validate(docs, source):
			log.info("validation failed; no migration attempted")
			return
		watch = Stopwatch()
		for doc in docs:
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
		existing = set(doc['filename'] for doc in
			self.coll.files.find(fields=['filename']))
		return tuple(
			doc for doc in source.coll.find()
			if self.__full_path(doc) not in existing
			and doc['_id'] not in self.bad_ids
		)

	def __validate(self, docs, source):
		"""
		Validate each of the records in the database (in advance)
		"""
		valid = True
		watch = Stopwatch()
		for doc in docs:
			if not '_mime' in doc:
				log.info("%s: no content type", doc['_id'])
				valid = False
			try:
				url = urlparse.urljoin(self.base, doc['_id'])
				req = MethodRequest(url, method='HEAD')
				urllib2.urlopen(req)
			except Exception:
				mongs_url = urllib2.quote('http://mongs.yougov.net/{server}/'
					'{database}/{collection}/{query}/1/'.format(
						server=source.coll.database.connection.host,
						database=source.coll.database.name,
						collection=source.coll.name,
						query='{"_id": "%s"}' % doc['_id'],
					), safe='/:',
				)
				log.info("error retrieving %s. check document at %s", url,
					mongs_url)
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

class CatalogMissingMigration(object):
	"""
	During the last attempted migration, we found that many of the resources
	on the filesystem are being referenced by at least some surveys. This
	migration script should be run on the filesystem-based airportlocker host.
	It will run through the filesystem and identify any resources that are
	not in the catalog and add them.
	"""
	@classmethod
	def get_args(cls):
		parser = argparse.ArgumentParser()
		parser.add_argument('--mongo-host',
			default=airportlocker.config.mongo_host)
		parser.add_argument('--filestore',
			default=airportlocker.config.filestore)
		args = parser.parse_args()
		airportlocker.config.update(vars(args))

	@classmethod
	def run(cls):
		"""
		Launch this migration from the command-line. Set config parameters
		using command-line options.
		"""
		cls.get_args()
		logging.basicConfig(level=logging.INFO)
		importlib.import_module('airportlocker.etc.startup')
		cls().backfill()

	def __init__(self):
		self.target = airportlocker.lib.gridfs.GridFSStorage()

	def backfill(self):
		source = airportlocker.lib.filesystem.FileStorage()
		for filepath in airportlocker.config.filestore.walkfiles():
			if filepath.endswith('.deleted'):
				continue
			relpath = airportlocker.config.filestore.relpathto(filepath)
			if source.exists(relpath):
				continue
			self.add_file(filepath)

	def add_file(self, filepath):
		#m_time = datetime.datetime.utcfromtimestamp(filepath.getmtime())
		target_path = airportlocker.config.filestore.relpathto(filepath)
		print("Adding missing file", target_path)
		type_, encoding = mimetypes.guess_type(filepath)
		if not type_:
			raise ValueError("Couldn't guess type of {0}".format(filepath))
		with filepath.open() as stream:
			self.target._save(stream, target_path, type_, meta={})
