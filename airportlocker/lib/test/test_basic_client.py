import os
import time
import yaml
import importlib

import httplib2
import pkg_resources
import cherrypy._cpserver
from fab.testing import FabBrowser

import airportlocker.control.root
from airportlocker.control.vr_launch import ConfigDict
from airportlocker.lib.client import AirportLockerClient

here = os.path.abspath(os.path.dirname(__file__))

def embed_server():
	config_file = pkg_resources.resource_filename(
		'airportlocker.lib', 'test/config.yaml')
	config_file = os.path.normpath(config_file)
	with open(config_file) as config_stream:
		airportlocker.config = ConfigDict(yaml.load(config_stream))
	importlib.import_module('airportlocker.etc.startup')
	airportlocker.control.root.start()

def wait_for_http(url):
	h = httplib2.Http()
	for t in range(50):
		resp, content = h.request(url)
		if resp.status == 200:
			break
		time.sleep(.5)
	else:
		raise RuntimeError("Unable to connect: %s" % resp)

class TestBasicClient(object):

	def setup_class(self):
		embed_server()
		# cherrypy started
		cherrypy._cpserver.wait_for_occupied_port('localhost', 8090)

		# fab templates loaded and other stuff ready
		wait_for_http('http://localhost:8090/_dev/')

		self.base_url = 'http://localhost:8090/'
		self.browser = FabBrowser()

	def teardown_class(self):
		cherrypy.engine.exit()

	def test_upload_file(self):
		client = AirportLockerClient(self.base_url, httplib2.Http())
		test_file = os.path.join(here, 'upload_test_file.txt')
		result = client.create(test_file, {'foo': 'bar'})
		print result
		assert result
		remote_file = client.read(result['value'])
		assert remote_file
		assert remote_file == open(test_file, 'r').read()
