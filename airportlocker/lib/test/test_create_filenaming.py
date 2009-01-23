import os
import shutil
import mimetypes

from StringIO import StringIO

import fab
import cherrypy
import py.test

from airportlocker.lib.resource import ResourceMixin
from eggmonster import env

env.filestore = os.path.dirname(os.path.abspath(__file__))

class MockResource(ResourceMixin):
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

class TestFileNaming(object):

	def setup_class(self):
		self.obj = MockResource()
		self.mfs = '.test_mockfilestore'
		env.filestore = self.mfs
		if not os.path.exists(self.mfs) or not os.path.isdir(self.mfs):
			os.mkdir(self.mfs)
		self.sample_filenames = [
			'foo.jpeg',
			'foo_bar.jpeg',
			'foo_bar_1.jpeg',
			'foo_bar__1.jpeg',
			'a/b/bar.jpeg',
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
			('hello world.doc', 'application/msword', 'hello world.doc'),
			('picture.jpg', JPEG, 'picture.jpg'),
			('yeah', JPEG, 'yeah.jpeg'),
			('YEAH.JPG', JPEG, 'YEAH.JPG'),
			('mytext.txt', TXT, 'mytext.txt'),
		]
		for fn, type, expected in filenames:
			assert self.obj.add_extension(fn, type) == expected

	def test_last_index(self):
		assert self.obj.get_next_index(self.mfs, 'new', JPEG) == None
		assert self.obj.get_next_index(self.mfs, 'foo', JPEG) == 1
		assert self.obj.get_next_index(self.mfs, 'foo_bar', JPEG) == 2
		
		# the initial file was removed so we can fill it in here
		assert self.obj.get_next_index(self.mfs, 'foo_bar_', JPEG) == None
		new_file = os.path.join(self.mfs, 'foo_bar_.jpeg')
		open(new_file, 'a').close()

		# now it should hit two
		assert self.obj.get_next_index(self.mfs, 'foo_bar_', JPEG) == 2
		os.remove(new_file)

	def test_verified_filename(self):
		# no files are written so the checks always return with the
		# original file comparisons
		new_names = [
			('foo', JPEG, 'foo_1.jpeg'),
			('foo bar ', JPEG, 'foo_bar_.jpeg'),
			('foo bar', JPEG, 'foo_bar_2.jpeg'),
			('foo@bar', JPEG, 'foo_bar_2.jpeg'),
			('foo!bar', JPEG, 'foo_bar_2.jpeg'),
			('foo?bar', JPEG, 'foo_bar_2.jpeg'),
			('foo+bar', JPEG, 'foo_bar_2.jpeg'),
			('foo*bar', JPEG, 'foo_bar_2.jpeg'),
			('foo#bar', JPEG, 'foo_bar_2.jpeg'),			
		]

		for fn, ext, expected in new_names:
			new_name = self.obj.verified_filename(self.mfs, fn, ext)
			assert new_name  == expected

	def test_file_io(self):
		fn = 'a_test_file.txt'
		fullpath = os.path.join(env.filestore, fn)
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
		os.remove(os.path.join(env.filestore, fn + '.deleted'))

		

			
