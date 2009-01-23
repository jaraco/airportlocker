import os
import re
import uuid
import mimetypes
import fab

from string import Template
from ottoman.lib.client import OttomanDocset # not used
from ottoman.model import DataStore, Database

from eggmonster import env

class LockerStore(DataStore):

	def __iter__(self):
		return iter(fab.pool('storage').get().list())

	def get(self, name):
		return self.dbs.setdefault(name, LockerDatabase(name))


class LockerDatabase(Database):
	def create_doc(self, key, value):
		fs = self.conn()
		fs.save(self.name, key, value)
		return key
	

class LockerFolder(object):
	clean_fn_regex = re.compile(r'[@\!\? \+\*\#]')
	index_re = re.compile(r'(.*)_(\d+).(.*)')

	def _has_extension(self, fn, ext):
		return os.path.splitext(fn)[1].lower() == ext

	def _get_extension(self, type, fn=None):
		exts = mimetypes.guess_all_extensions(type)
		if exts:
			if fn:
				cur_ext = os.path.splitext(fn)[1]
				if cur_ext.lower() in exts:
					return cur_ext.lower()
			# take the last one
			return exts[-1]
		return '.uknown'

	def _add_extension(self, fn, type, index=None):
		ext = self._get_extension(type, fn)
		if not self._has_extension(fn, ext):
			parts = [fn, '_%s' % index if index else '']
			if not ext.startswith('.'):
				parts.append('.')
			parts.append(ext)
			fn = ''.join(parts)
		else:
			if index:
				fn = '%s_%s%s' % (fn[:-len(ext)], index, ext)
		return fn

	def _valid_key(self, fn, type):
		fullkey = self._add_extension(fn, type)
		fullpath = os.path.join(env.filestore)
		if not os.path.exists(fullpath):
			return fullkey
		ext = self._get_extension(type, fn) # this includes the '.'		
		exists = True
		cur_index = 1
		regex = '(.*)%s_(\d+).%s$' % (fn, ext)
		fexp = re.compile(regex)
		for root, dirs, fnames in os.walk(env.filestore):
			for fname in fnames:
				cur_fn = os.path.join(root, fname)
				match = fexp.match(cur_fn)
				if match:
					indexes.append(int(match.groups()[1]))
		if indexes:
			return max(indexes) + 1
		return cur_key

	def conn(self):
		pass # not necessary... 

	def get_by_id(self, key):
		return Database.get_by_id(self, key, json=False)

	def create_doc(self, key, value):
		valid_key = self._valid_key(key, value.type)
		fs.save(self.name, valid_key, value.file.read())
		return valid_key

	def read(self, key):
		return self.get_by_id(key, json=False)
			


class LockerView(object):
	def __init__(self, field):
		self.field = field
		self.code = Template('''
def filter(i, val):
	if '$key' in i and i['$key'] == val:
		return i
''')

	def code(self):
		return self.code.safe_substitute({'key': self.field})

class Locker(OttomanDocset):

	@property
	def all(self):
		return [i[1] for i in self]

	def delete(self, id):
		oid = self[id]
		if oid:
			return OttomanDocset.delete(self, oid.keys()[0])
		return False

	def by_view(self, name, *args):
		vname = 'by_%s' % name
		try:
			return self.view(vname, *args)
		except:
			view = LockerView(name)
			self.define_view(vname, view.code())
		return self.view(vname, *args)

	def __getitem__(self, key):
		return self.view('by_id', key)

	def __init__(self, *args, **kw):
		OttomanDocset.__init__(self, *args, **kw)
		self.define_view('by_id',
'''
def filter(i, id):
	if i['_id'] == id:
		return i
''')



