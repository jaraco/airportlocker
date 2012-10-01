import os
import itertools

import bson

import airportlocker

class NotFoundError(Exception): pass

class Storage(object):
	def find(self, *args, **kwargs):
		return self.coll.find(*args, **kwargs)

	def find_one(self, *args, **kwargs):
		return self.coll.find_one(*args, **kwargs)

	def exists(self, id):
		return bool(self.find_one(self.by_id(id)))

	@staticmethod
	def by_id(id):
		"""
		Create a query to find a record by id (result will be passed as the
		first argument to self.find_one).

		If ID looks like an ObjectID, construct one. Otherwise, use the string
		directly.

		When UUIDs have all been converted to ObjectIds, then the trap for
		the exception can be removed.
		"""
		try:
			id = bson.objectid.ObjectId(id)
		except Exception:
			pass
		return id

	@property
	def coll(self):
		return airportlocker.store[airportlocker.config.docset]

def numbered_files(filepath, format="{name}_{num}{ext}"):
	"""
	Return variants of the filepath with numbers appended.

	One may supply a format string indicating the format of the result, which
	takes the following fields:
		- name (the name of the file without extension)
		- num (the index generated)
		- ext (the extension)

	>>> list(itertools.islice(numbered_files('foo.bar'), 3))
	['foo.bar', 'foo_1.bar', 'foo_2.bar']
	"""
	yield filepath
	name, ext = os.path.splitext(filepath)
	if name.endswith('.tar'):
		# special case - .tar.*
		name, _ = os.path.splitext(filepath)
		ext = '.tar' + ext
	for num in itertools.count(1):
		yield format.format(**vars())

def unique_name(candidates, exists):
	"""
	Given a series of candidate names and a function that checks for
	existence, return the first name that doesn't exist.

	>>> exist_fn = lambda fn: fn in ('file.txt', 'file_1.txt')
	>>> unique_name(numbered_files('some file.txt'), exist_fn)
	'some file.txt'
	>>> unique_name(numbered_files('file.txt'), exist_fn)
	'file_2.txt'
	>>> candidates = numbered_files('file.txt', format='{name} ({num}){ext}')
	>>> unique_name(candidates, exist_fn)
	'file (1).txt'
	"""
	return next(itertools.ifilterfalse(exists, candidates))
