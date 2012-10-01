from __future__ import absolute_import, unicode_literals

import os

import gridfs

from . import storage

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
		meta['content_type'] = cp_file.content_type
		return unicode(
			self.fs.put(cp_file.file, filename=filename, **meta)
		)

	def update(self, id, meta, cp_file=None):
		"""
		Update the document identified by id with the new metadata and file
		(if supplied).
		"""
		# stubbed

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
