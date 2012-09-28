import os
import shutil
import io

import py.test

import airportlocker.lib.filesystem

class MockStorage(airportlocker.lib.filesystem.FileStorage):
	pass


class MockFileObj(object):
	def __init__(self, fn, contents):
		self.file = io.BytesIO()
		self.file.write('\n'.join(contents))
		self.file.seek(0)
		self.filename = fn
		self.type = 'text/plain'

	def __iter__(self):
		self.file.seek(0)
		for l in self.file.readlines():
			yield l

JPEG = 'image/jpeg'
DOC = 'application/msword'
TXT = 'text/plain'
ZIP = 'application/zip'
M4V = 'video/m4v'

class TestFileNaming(object):

	def setup_class(self):
		self.storage = MockStorage()
		self.mfs = '.test_mockfilestore'
		airportlocker.filestore = self.mfs
		if not os.path.isdir(self.mfs):
			os.mkdir(self.mfs)
		self.sample_filenames = [
			'foo.jpg',
			'foo_bar.jpg',
			'foo_bar_1.jpg',
			'foo_bar__1.jpg',
			'a/b/bar.jpg',
			'x/y/z.m4v',
		]
		for fn in self.sample_filenames:
			if os.path.dirname(fn):
				os.makedirs(os.path.join(self.mfs, os.path.dirname(fn)))
			open(os.path.join(self.mfs, fn), 'a').close()

	def teardown_class(self):
		shutil.rmtree(self.mfs)

	def test_exists(self):
		for filename in self.sample_filenames:
			assert self.storage.exists(filename)
		for filename in ['welcome', 'enough']:
			assert not self.storage.exists(filename)

	def test_verified_filename(self):
		# no files are written so the checks always return with the
		# original file comparisons
		new_names = [
			('foo.jpg', 'foo_1.jpg'),
			('foo bar .jpg', 'foo_bar_.jpg'),
			('foo bar.jpg', 'foo_bar_2.jpg'),
			('foo@bar.jpg', 'foo_bar_2.jpg'),
			('foo!bar.jpg', 'foo_bar_2.jpg'),
			('foo?bar.jpg', 'foo_bar_2.jpg'),
			('foo+bar.jpg', 'foo_bar_2.jpg'),
			('foo*bar.jpg', 'foo_bar_2.jpg'),
			('foo#bar.jpg', 'foo_bar_2.jpg'),
		]

		for fn, expected in new_names:
			new_name = self.storage.verified_filename(fn)
			assert new_name == expected

	def test_file_io(self):
		fn = 'a_test_file.txt'
		fullpath = os.path.join(airportlocker.filestore, fn)
		contents = [str(x) for x in range(1, 20)]
		fake_file = MockFileObj(fn, contents)
		self.storage.save_file(fake_file)
		assert os.path.exists(fullpath)

		contents2 = [str(x) for x in range(2, 22, 2)]
		contents2_str = '\n'.join(contents2)
		update_file = MockFileObj(fn, contents2)
		self.storage.update_file(fn, update_file)
		updated_content = open(fullpath).read()
		assert updated_content == contents2_str

		self.storage.remove_file(fn)
		assert not os.path.exists(fullpath)
		assert os.path.exists(fullpath + '.deleted')
		os.remove(os.path.join(airportlocker.filestore, fn + '.deleted'))
