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
		meta['name'] = filename
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
		pass # stubbed

	def delete(self, id):
		pass # stubbed
