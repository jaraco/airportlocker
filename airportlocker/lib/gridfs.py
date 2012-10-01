from __future__ import absolute_import, unicode_literals

import os

import gridfs

from . import storage
import airportlocker

class GridFSStorage(storage.Storage):
	'''
	A mix-in class to be used with Resource controller objects providing
	gridfs-backed resource file storage.
	'''

	@property
	def fs(self):
		return gridfs.GridFS(self.coll.database, self.coll.name)

	def verified_filename(self, fn):
		'''
		Return a unique, human-readable filename that's safe to save to the
		filesystem.
		'''
		return storage.unique_name(storage.numbered_files(fn), self.exists)

	def exists(self, filepath):
		"""
		Return True iff filepath already exists in the filestore.
		"""
		return self.fs.exists(filename=filepath)

	def save(self, cp_file, name, meta):
		prefix = meta.pop('_prefix', '')
		prefix = prefix.rstrip('/')
		filename = os.path.join(prefix, name or cp_file.filename)
		filename = self.verified_filename(filename)
		return unicode(self._save(cp_file.file, filename=filename,
			content_type=cp_file.content_type, **meta))

	def _save(self, stream, filename, content_type, meta):
		return self.fs.put(stream, filename=filename,
			content_type=content_type, **meta)

	def update(self, id, meta, cp_file=None):
		"""
		Update the document identified by id with the new metadata and file
		(if supplied).
		Return the updated metadata.
		"""
		if not self.exists(id):
			raise storage.NotFoundError(id)

		if cp_file:
			return self.replace_file(id, meta, cp_file)

		# don't allow overriding of these keys
		for key in ('_id', '_filename', 'name'):
			meta.pop(key, None)
		spec = dict(_id=self.by_id(id))
		self.coll.files.update(spec, {"$set": meta})
		new_doc = self.find_one(self.by_id(id))
		return new_doc

	def replace_file(self, id, meta, cp_file):
		"""
		GridFS doesn't easily enable overriding an existing file, so we do
		the work here. id must exist.

		Saves the new file, removes the old file.

		Return the newly-created doc (which will have a new id).

		This behavior was created to match the FileStorage implementation.
		Consider re-defining the meaning of .update to be more
		straightforward.
		"""
		new_id = self.save(cp_file, None, meta)
		self.delete(id)
		return self.fs.get(self.by_id(new_id))._file

	def get_resource(self, key):
		"""
		Retrieve a resource by key (file path or unique ID).
		Returns the document stream and content type.
		"""
		if self.fs.exists(filename=key):
			file = self.fs.get_last_version(key)
		elif self.fs.exists(self.by_id(key)):
			file = self.fs.get(self.by_id(key))
		else:
			raise storage.NotFoundError(key)
		return file, file.content_type

	def delete(self, id):
		"""
		Delete the file indicated by id. Return the metadata for the deleted
		document or an empty dict if the id did not exist.
		"""
		try:
			id = self.by_id(id)
			meta = self.fs.get(id)._file
			self.fs.delete(id)
		except gridfs.errors.NoFile:
			return {}
		return meta

	@classmethod
	def migrate(cls, mongodb_url, file_store):
		"""
		Migrate the data from a FileStorage instance.
		"""
		import pymongo
		from airportlocker.control.vr_launch import ConfigDict
		from airportlocker.lib import filesystem
		import posixpath
		airportlocker.store = pymongo.Connection(mongodb_url).airportlocker
		airportlocker.config = ConfigDict(
			docset = 'luggage',
		)
		airportlocker.filestore = file_store
		source = filesystem.FileStorage()
		dest = cls()
		# first validate
		if not cls.validate(source):
			return
		for doc in source.coll.find():
			filename = posixpath.join(doc.get('_prefix', ''),
				doc['_filename'])
			content_type = doc['_mime']
			meta = dict(
				(k,v) for k,v in doc.items()
				if not k.startswith('_') and k != 'name'
			)
			with open(os.path.join(source.root, filename), 'rb') as f:
				dest._save(f, filename, content_type, meta)

	@classmethod
	def validate(cls, source):
		import posixpath
		valid = True
		for doc in source.coll.find():
			filename = posixpath.join(source.root, doc.get('_prefix', ''),
				doc['_filename'])
			content_type = doc['_mime']
			if not os.path.isfile(filename):
				print(filename, "doesn't exist")
				valid = False
		return valid
