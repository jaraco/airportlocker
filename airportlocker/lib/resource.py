import re
import os
from mimetypes import guess_type, guess_all_extensions

class ResourceMixin(object):

	clean_fn_regex = re.compile(r'[@\!\? \+\*\#]')
	index_re = re.compile(r'(.*)_(\d+).(.*)')


	def get_extension(self, type, fn=None):
		exts = guess_all_extensions(type)
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

	def add_extension(self, fn, type):
		ext = self.get_extension(type, fn)
		if not self.has_extension(fn, ext):
			parts = [fn]
			if not ext.startswith('.'):
				parts.append('.')
			parts.append(ext)
			fn = ''.join(parts)
		return fn

	def get_next_index(self, folder, fn, type):
		fullpath = self.add_extension(os.path.join(folder, fn), type)
		if not os.path.exists(fullpath) or not os.path.isfile(fullpath):
			return None
		ext = self.get_extension(type, fn) # this includes the '.'
		regex = '(.*)%s_(\d+)%s$' % (fn, ext)
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
		if index:
			fn = '%s_%s' % (fn, index)
		return self.add_extension(fn, type)
		
	def save_file(self, folder, fs, name=None):
		fn = self.verified_filename(folder, name or fs.filename, fs.type)
		path = os.path.join(folder, fn)
		dirname = os.path.dirname(path)
		if not os.path.exists(dirname) or not os.path.isdir(dirname):
			os.makedirs(dirname)
		newfile = open(path, 'w+')
		for chunk in fs.file:
			newfile.write(chunk)
		newfile.close()
		return fn
