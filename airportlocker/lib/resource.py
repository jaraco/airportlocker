import re
import os
from mimetypes import guess_type, guess_all_extensions

class ResourceMixin(object):

	clean_fn_regex = re.compile(r'[@\!\? \+\*\#]')
	index_re = re.compile(r'(.*)_(\d+).(.*)')

	def add_extension(self, fn, ext):
		if not fn.endswith(ext):
			parts = [fn]
			if not ext.startswith('.'):
				parts.append('.')
			parts.append(ext)
			fn = ''.join(parts)
		return fn

	def get_next_index(self, folder, fn, ext):
		fullpath = self.add_extension(os.path.join(folder, fn), ext)
		if not os.path.exists(fullpath) or not os.path.isfile(fullpath):
			return None
		if ext.startswith('.'):
			ext = ext[1:]
		regex = '(.*)%s_(\d+).%s$' % (fn, ext)
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
		ext = guess_all_extensions(type)
		if ext:
			# take the last one
			ext = ext.pop()
		else:
			ext = '.unknown'
		fn = self.clean_fn_regex.sub('_', fn)
		index = self.get_next_index(folder, fn, ext)
		if index:
			fn = '%s_%s' % (fn, index)
		return self.add_extension(fn, ext)
		
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
