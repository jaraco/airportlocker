import mimetypes
mimetypes.init()
mimetypes.add_type('video/m4v', '.m4v')
mimetypes.add_type('audio/m4a', '.m4a')

import re
import os
import cherrypy

from eggmonster import env


class ResourceMixin(object):
	'''This mixin provides the filesystem interface for working with
	resource files.'''

	clean_fn_regex = re.compile(r'[@\!\? \+\*\#]')
	index_re = re.compile(r'(.*)_(\d+).(.*)')

	def get_extension(self, mtype, fn=None):
 		if mtype == 'none' and fn:
 			mtype, e = mimetypes.guess_type(fn)
		exts = mimetypes.guess_all_extensions(mtype)
		if exts:
			if fn:
				cur_ext = os.path.splitext(fn)[1]
				if cur_ext.lower() in exts:
					return cur_ext.lower()
			# take the last one
			return exts[-1]
		return '.uknown'

	def has_extension(self, fn, ext):
		return os.path.splitext(fn)[1].lower() == ext

	def rm_ext(self, fn, ext):
		'''Removes the extension for use in other algorithms'''
		if not ext.startswith('.'):
			ext = '.' + ext
		m = re.match(r'(.*)(\%s|\%s)' % (ext, ext.upper()), fn)
		if m:
			return m.groups()[0]
		return fn

	def add_extension(self, fn, type, index=None):
		'''Unwraps the file name so we can append the next number in
		the sequence.'''
		ext = self.get_extension(type, fn)
		if self.has_extension(fn, ext):
			fn = self.rm_ext(fn, ext)
		parts = [fn]
		if index:
			parts.append('_%s' % index)
		if not ext.startswith('.'):
			parts.append('.')
		parts.append(ext)
		fn = ''.join(parts)
		return fn

	def get_next_index(self, folder, fn, type):
		'''Gets the next number to uniquify a filename:
		1. Check if the file exists if not return
		2. Loop through files looking for matches on the filename pattern
		3. Any matches, add the integer to a list
		4. If there are any listed numbers, get the max and add 1
		5. Return 1 since it is the first duplicate'''
		
		fullpath = self.add_extension(os.path.join(folder, fn), type)
		if not os.path.exists(fullpath) or not os.path.isfile(fullpath):
			return None
		ext = self.get_extension(type, fn) # this includes the '.'
		regex = '(.*)%s_(\d+)%s$' % (self.rm_ext(fn, ext), ext)
		fexp = re.compile(regex)
		indexes = []
		for root, dirs, fnames in os.walk(folder):
			for fname in fnames:
				cur_fn = os.path.join(root, fname)
				match = fexp.match(cur_fn)
				if match:
					indexes.append(int(match.groups()[1]))
		if indexes:
			return max(indexes) + 1
		return 1

	def verified_filename(self, folder, fn, type):
		'''Returns a unique human readable filename (ie not a uuid)'''
		fn = self.clean_fn_regex.sub('_', fn)
		index = self.get_next_index(folder, fn, type)
		return self.add_extension(fn, type, index)
		
	def save_file(self, fs, name=None):
		folder = env.filestore
		mtype, e = mimetypes.guess_type(fs.filename)
		fn = self.verified_filename(folder, name or fs.filename, mtype)
		path = os.path.join(folder, fn)
		self._write_file(path, fs.file)
		return fn

	def _write_file(self, path, fh):
		dirname = os.path.dirname(path)
		if not os.path.exists(dirname) or not os.path.isdir(dirname):
			os.makedirs(dirname)
		newfile = open(path, 'w+')
		for chunk in fh:
			newfile.write(chunk)
		newfile.close()

	def update_file(self, fn, fh):
		path = os.path.join(env.filestore, fn)
		self._write_file(path, fh)

	def get_resource(self, key):
		resource = None
		ct = 'application/octet-stream'
		fullpath = os.path.join(env.filestore, key)
		if os.path.exists(fullpath) and os.path.isfile(fullpath):
			resource = open(fullpath, 'r')
			ct, enc = mimetypes.guess_type(key)
		else:
			try:
				doc = self.db.get_by_id(key)
			except KeyError:
				raise cherrypy.HTTPError(404)
			fullpath = os.path.join(env.filestore, doc['name'])
			if os.path.exists(fullpath) and os.path.isfile(fullpath):
				resource = open(fullpath)
				ct = doc['_mime']
			else:
				raise cherrypy.HTTPError(404)
		return resource, ct

	def remove_file(self, fn):
		'''We do not actually remove the file. We just add a "deleted"
		extension. Clean up can be done via cron if necessary.'''
		path = os.path.join(env.filestore, fn)
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
		
