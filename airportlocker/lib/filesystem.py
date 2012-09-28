import re
import os
import mimetypes
import platform

import cherrypy

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

	def save(self, cp_file, name, meta):
		# save the file and grab its name
		meta['_filename'] = self.save_file(cp_file, name,
			prefix=meta.get('_prefix'))
		meta['name'] = meta['_filename']
		meta['_mime'] = cp_file.type
		inserted_id = self.coll.insert(meta)
		return inserted_id

	def save_file(self, fs, name=None, prefix=None):
		"""
		Save the CherryPy File object fs to self.root/prefix
		"""
		prefix = prefix or ''
		if prefix.endswith('/'):
			prefix = prefix[:-1]
		filepath = os.path.join(prefix, name or fs.filename)
		filepath = self.verified_filename(filepath)
		filepath = self._ensure_extension(filepath, fs.filename)
		self._write_file(filepath, fs.file)
		return os.path.basename(filepath)

	@staticmethod
	def _ensure_extension(filename, source_filename):
		"""
		Ensure the filename has an extension and that it matches the source
		filename. If it doesn't, append the extension from the source
		filename. This method is for backward compatibility, matching previous
		behavior where a user can supply a name but the name need not include
		the extension.

		>>> FileStorage._ensure_extension('foo', 'foo.txt')
		'foo.txt'
		>>> FileStorage._ensure_extension('foo.jpg', 'foo.JPG')
		'foo.jpg'

		It should work too if the extensions resolve to the same mime type.
		>>> FileStorage._ensure_extension('foo.jpg', 'foo.jpeg')
		'foo.jpg'

		It might look weird, but if the filename has an incorrect extension,
		differing from the source_filename, the source takes precedence.
		>>> FileStorage._ensure_extension('foo.txt', 'my file.jpeg')
		'foo.txt.jpeg'
		"""
		_, source_ext = os.path.splitext(source_filename)
		guess = mimetypes.guess_type
		if guess(filename) != guess(source_filename):
			filename += source_ext
		return filename

	def _write_file(self, target, stream):
		"""
		Write stream to target in self.root
		"""
		target = os.path.join(self.root, target)
		dirname = os.path.dirname(target)
		if not os.path.isdir(dirname):
			os.makedirs(dirname)
		with open(target, 'w+') as newfile:
			for chunk in stream:
				newfile.write(chunk)

	update_file = _write_file

	def update(self, id, meta, cp_file=None):
		cur_doc = self.find_one(dict(_id=id))
		if not cur_doc:
			raise storage.NotFoundError(id)

		# copy values from current document (overriding any values supplied
		# by the query).
		meta['_id'] = cur_doc['_id']
		meta['_filename'] = cur_doc['_filename']
		meta['name'] = cur_doc['name']
		if cp_file:
			meta['_mime'] = cp_file.type or cur_doc['_mime']
		spec = dict(_id=id)
		self.coll.update(spec, meta)
		new_doc = self.find_one(dict(_id=id))
		if cp_file:
			self.update_file(new_doc['name'], cp_file.file)
		return new_doc

	def get_resource(self, key):
		resource = None
		ct = 'application/octet-stream'
		fullpath = os.path.join(airportlocker.filestore, key)
		if os.path.exists(fullpath) and os.path.isfile(fullpath):
			resource = open(fullpath, 'r')
			ct, enc = mimetypes.guess_type(key)
		else:
			doc = self.coll.find_one(key)
			if doc is None:
				raise cherrypy.HTTPError(404)
			fullpath = os.path.join(airportlocker.filestore,
				doc.get('_prefix', ''), doc['name'])
			if not os.path.isfile(fullpath):
				raise cherrypy.HTTPError(404)
			resource = open(fullpath)
			ct = doc['_mime']
		return resource, ct

	def delete(self, id):
		meta = self.coll.find_one(dict(_id=id)) or {}
		if meta:
			self.remove_file(meta['name'])
			self.coll.remove(id)
		return meta

	def remove_file(self, fn):
		'''We do not actually remove the file. We just add a "deleted"
		extension. Clean up can be done via cron if necessary.'''
		path = os.path.join(airportlocker.filestore, fn)
		if os.path.exists(path) and os.path.isfile(path):
			os.rename(path, '%s.deleted' % path)

	def return_file(self, path):
		resource, ct = self.get_resource(path)
		if not resource:
			raise cherrypy.HTTPError(404)
		cherrypy.response.headers.update({
			'Content-Type': ct or 'text/plain',
		})
		return resource

	def head_file(self, path):
		resource, ct = self.get_resource(path)
		if not resource:
			raise cherrypy.HTTPError(404)
		size = sum([len(l) for l in resource])
		cherrypy.response.headers.update({
			'Content-Type': ct or 'text/plain',
			'Content-Length': size,
		})
		return
