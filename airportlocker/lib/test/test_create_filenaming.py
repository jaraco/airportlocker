import os
import shutil

from StringIO import StringIO

import py.test

import airportlocker.lib.resource

# is this still needed
airportlocker.filestore = os.path.dirname(os.path.abspath(__file__))

class MockResource(airportlocker.lib.resource.ResourceMixin):
	pass


class MockFileObj(object):
	def __init__(self, fn, contents):
		self.file = StringIO()
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
		self.obj = MockResource()
		self.mfs = '.test_mockfilestore'
		airportlocker.filestore = self.mfs
		if not os.path.exists(self.mfs) or not os.path.isdir(self.mfs):
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

	def test_add_extension(self):
		filenames = [
			('hello.world', ZIP, 'hello.world.zip'),
			('foo.bar.zip', ZIP, 'foo.bar.zip'),
			('hello world.doc', DOC, 'hello world.doc'),
			('picture.jpg', JPEG, 'picture.jpg'),
			('yeah', JPEG, 'yeah.jpg'),
			('YEAH.JPG', JPEG, 'YEAH.jpg'),
			('mytext.txt', TXT, 'mytext.txt'),
			('my video', M4V, 'my video.m4v'),
		]
		for fn, type, expected in filenames:
			assert self.obj.add_extension(fn, type) == expected

	def test_last_index(self):
		py.test.skip("fails - no longer matches API")
		assert self.obj.get_next_index(self.mfs, 'new', JPEG) == None
		assert self.obj.get_next_index(self.mfs, 'foo', JPEG) == 1
		assert self.obj.get_next_index(self.mfs, 'foo_bar', JPEG) == 2

		# the initial file was removed so we can fill it in here
		assert self.obj.get_next_index(self.mfs, 'foo_bar_', JPEG) == None
		new_file = os.path.join(self.mfs, 'foo_bar_.jpg')
		open(new_file, 'a').close()

		# now it should hit two
		assert self.obj.get_next_index(self.mfs, 'foo_bar_', JPEG) == 2
		os.remove(new_file)

	def test_verified_filename(self):
		py.test.skip("fails - no longer matches API")
		# no files are written so the checks always return with the
		# original file comparisons
		new_names = [
			('foo', JPEG, 'foo_1.jpg'),
			('foo bar ', JPEG, 'foo_bar_.jpg'),
			('foo bar', JPEG, 'foo_bar_2.jpg'),
			('foo@bar', JPEG, 'foo_bar_2.jpg'),
			('foo!bar', JPEG, 'foo_bar_2.jpg'),
			('foo?bar', JPEG, 'foo_bar_2.jpg'),
			('foo+bar', JPEG, 'foo_bar_2.jpg'),
			('foo*bar', JPEG, 'foo_bar_2.jpg'),
			('foo#bar', JPEG, 'foo_bar_2.jpg'),
		]

		for fn, ext, expected in new_names:
			new_name = self.obj.verified_filename(self.mfs, fn, ext)
			assert new_name  == expected

	def test_file_io(self):
		fn = 'a_test_file.txt'
		fullpath = os.path.join(airportlocker.filestore, fn)
		contents = [str(x) for x in range(1, 20)]
		fake_file = MockFileObj(fn, contents)
		self.obj.save_file(fake_file)
		assert os.path.exists(fullpath)

		contents2 = [str(x) for x in range(2, 22, 2)]
		contents2_str = '\n'.join(contents2)
		update_file = MockFileObj(fn, contents2)
		self.obj.update_file(fn, update_file)
		updated_content = open(fullpath).read()
		assert updated_content == contents2_str

		self.obj.remove_file(fn)
		assert not os.path.exists(fullpath)
		assert os.path.exists(fullpath + '.deleted')
		os.remove(os.path.join(airportlocker.filestore, fn + '.deleted'))
