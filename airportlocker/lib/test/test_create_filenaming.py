import os
import shutil
import io

import py.test

import airportlocker.lib.filesystem

class MockStorage(airportlocker.lib.filesystem.FileStorage):
	pass


JPEG = 'image/jpeg'
DOC = 'application/msword'
TXT = 'text/plain'
ZIP = 'application/zip'
M4V = 'video/m4v'

class TestFileNaming(object):
	@classmethod
	def setup_class(cls):
		cls.storage = MockStorage()
		cls.mfs = '.test_mockfilestore'
		airportlocker.filestore = cls.mfs
		if not os.path.isdir(cls.mfs):
			os.mkdir(cls.mfs)
		cls.sample_filenames = [
			'foo.jpg',
			'foo_bar.jpg',
			'foo_bar_1.jpg',
			'foo_bar__1.jpg',
			'a/b/bar.jpg',
			'x/y/z.m4v',
		]
		for fn in cls.sample_filenames:
			if os.path.dirname(fn):
				os.makedirs(os.path.join(cls.mfs, os.path.dirname(fn)))
			open(os.path.join(cls.mfs, fn), 'a').close()

	@classmethod
	def teardown_class(cls):
		shutil.rmtree(cls.mfs)

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
		expected_save_file = os.path.join(airportlocker.filestore, fn)
		contents = [str(x) for x in range(1, 20)]
		fake_file = io.BytesIO(''.join(contents))
		self.storage._write_file(fn, fake_file)
		assert os.path.exists(expected_save_file)

		contents2 = [str(x) for x in range(2, 22, 2)]
		update_file = io.BytesIO('\n'.join(contents2))
		self.storage._write_file(fn, update_file)
		with open(expected_save_file) as f:
			updated_content = f.read()
		assert updated_content == update_file.getvalue()

		self.storage.remove_file(fn)
		assert not os.path.exists(expected_save_file)
		assert os.path.exists(expected_save_file + '.deleted')
		os.remove(os.path.join(airportlocker.filestore, fn + '.deleted'))
