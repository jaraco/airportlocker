import os
import shutil
import mimetypes

import fab
import cherrypy
import py.test

from airportlocker.lib.resource import ResourceMixin

class MockResource(ResourceMixin):
	pass

JPEG = 'image/jpeg'
DOC = 'application/msword'
TXT = 'text/plain'
ZIP = 'application/zip'

class TestFileNaming(object):

	def setup_class(self):
		self.obj = MockResource()
		self.mfs = '.test_mockfilestore'
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
			
