import re
import os
import mimetypes
import platform
import sys

import airportlocker
from . import storage

if platform.system() != 'Windows':
	# Only init on non-Windows because the Windows registry doesn't have
	#  proper IANA types (i.e. zip~=application/x-zip-compressed)
	mimetypes.init()
mimetypes.add_type('video/m4v', '.m4v')
mimetypes.add_type('audio/m4a', '.m4a')
mimetypes.add_type('text/csv', '.csv')

class FileStorage(storage.Storage):
	'''
	A mix-in class to be used with Resource controller objects providing
	filesystem-backed resource file storage.
	'''

	bad_filename_chars = re.compile(r'[@\!\? \+\*\#]')
	"Characters that get replaced with underscores"

	@classmethod
	def startup(cls):
		filestore = airportlocker.config.filestore
		filestore = filestore.replace('{prefix}', sys.prefix)
		filestore = filestore.replace('/usr/var', '/var')
		if not os.path.isdir(filestore):
			os.makedirs(filestore)
		airportlocker.filestore = filestore

	def verified_filename(self, fn):
		'''
		Return a unique, human-readable filename that's safe to save to the
		filesystem.
		'''
		fn = self.bad_filename_chars.sub('_', fn)
		return storage.unique_name(storage.numbered_files(fn), self.exists)

	def exists(self, filepath):
		"""
		Return True iff filepath already exists in the filestore.
		"""
		fullpath = os.path.join(self.root, filepath)
		return os.path.exists(fullpath)

	@property
	def root(self):
		return airportlocker.filestore

	def save(self, stream, filepath, content_type, meta):
		filepath = self.verified_filename(filepath)
		self._write_file(filepath, stream)

		prefix, filename = os.path.split(filepath)
		# for compatibility, store filepath as _prefix and _filename
		meta['name'] = meta['_filename'] = filename
		meta['_prefix'] = prefix
		meta['_mime'] = content_type
		inserted_id = self.coll.insert(meta)
		return unicode(inserted_id)

	def _write_file(self, target, stream):
		"""
		Write stream to target in self.root
		"""
		target = os.path.join(self.root, target)
		dirname = os.path.dirname(target)
		if not os.path.isdir(dirname):
			os.makedirs(dirname)
		with open(target, 'w+b') as newfile:
			for chunk in stream:
				newfile.write(chunk)

	update_file = _write_file

	def update(self, id, meta, cp_file=None):
		"""
		Update the document identified by id with the new metadata and file
		(if supplied).
		Return the updated metadata.
		"""
		if not self.coll.find_one(id):
			raise storage.NotFoundError(id)

		# don't allow overriding of these keys
		for key in ('_id', '_filename', 'name'):
			meta.pop(key, None)
		if cp_file and cp_file.type:
			meta['_mime'] = cp_file.type
		spec = dict(_id=self.by_id(id))
		self.coll.update(spec, {"$set": meta})
		new_doc = self.find_one(self.by_id(id))
		if cp_file:
			self.update_file(new_doc['name'], cp_file.file)
		return new_doc

	def get_resource(self, key):
		"""
		Retrieve a resource by key (either by file path or unique ID).
		Returns the document stream and content type.
		"""
		fullpath = os.path.join(airportlocker.filestore, key)
		if os.path.isfile(fullpath):
			resource = open(fullpath, 'rb')
			ct, enc = mimetypes.guess_type(key)
		else:
			doc = self.coll.find_one(self.by_id(key))
			if doc is None:
				raise storage.NotFoundError(key)
			fullpath = os.path.join(airportlocker.filestore,
				doc.get('_prefix', ''), doc['name'])
			if not os.path.isfile(fullpath):
				raise storage.NotFoundError(key)
			resource = open(fullpath)
			ct = doc['_mime']
		return resource, ct

	def delete(self, id):
		"""
		Delete the file indicated by id. Return the metadata for the deleted
		document or an empty dict if the id did not exist.
		"""
		meta = self.coll.find_one(self.by_id(id)) or {}
		if meta:
			# TODO - what about the prefix?
			self.remove_file(meta['name'])
			self.coll.remove(id)
		return meta

	def remove_file(self, fn):
		'''We do not actually remove the file. We just add a "deleted"
		extension. Clean up can be done via cron if necessary.'''
		path = os.path.join(airportlocker.filestore, fn)
		if os.path.isfile(path):
			os.rename(path, '%s.deleted' % path)
