import os
import shutil
import mimetypes

import fab
import cherrypy
import py.test

from airportlocker.lib.resource import ResourceMixin

class MockResource(ResourceMixin):
	pass

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
			('hello.world', '.zip', 'hello.world.zip'),
			('foo.bar.zip', '.zip', 'foo.bar.zip'),
			('hello world.doc', 'doc', 'hello world.doc'),
			('picture.jpg', 'jpg', 'picture.jpg'),
			('yeah', '.jpg', 'yeah.jpg'),
			('yeah', 'jpg', 'yeah.jpg'),
			('YEAH.JPG', 'jpg', 'YEAH.jpg'),
		]
		for fn, ext, expected in filenames:
			assert self.obj.add_extension(fn, ext) == expected

	def test_last_index(self):
		assert self.obj.get_next_index(self.mfs, 'new', '.jpeg') == None
		assert self.obj.get_next_index(self.mfs, 'foo', '.jpeg') == 1
		assert self.obj.get_next_index(self.mfs, 'foo_bar', '.jpeg') == 2
		# the initial file was removed so we can fill it in here
		assert self.obj.get_next_index(self.mfs, 'foo_bar_', '.jpeg') == None
		open(os.path.join(self.mfs, 'foo_bar_.jpeg'), 'a').close()
		# now it should hit two
		assert self.obj.get_next_index(self.mfs, 'foo_bar_', '.jpeg') == 2

	def test_verified_filename(self):
		new_names = [
			('foo', 'image/jpeg', 'foo_1.jpeg'),
			('foo bar', 'image/jpeg', 'foo_bar_2.jpeg'),
			('foo bar ', 'image/jpeg', 'foo_bar__2.jpeg'),
			('foo@bar', 'image/jpeg', 'foo_bar_3.jpeg'),
			('foo!bar', 'image/jpeg', 'foo_bar_4.jpeg'),
			('foo?bar', 'image/jpeg', 'foo_bar_5.jpeg'),
			('foo+bar', 'image/jpeg', 'foo_bar_6.jpeg'),
			('foo*bar', 'image/jpeg', 'foo_bar_7.jpeg'),
			('foo#bar', 'image/jpeg', 'foo_bar_8.jpeg'),			
		]

		for fn, ext, expected in new_names:
			new_name = self.obj.verified_filename(self.mfs, fn, ext)
			assert new_name  == expected
			
