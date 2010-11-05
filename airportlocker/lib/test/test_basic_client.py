import os
import time
import httplib2
from cherrypy._cpserver import wait_for_occupied_port
from threading import Thread
from eggmonster import runner

from fab.testing import FabBrowser

from airportlocker.lib.client import AirportLockerClient

here = os.path.abspath(os.path.dirname(__file__))

class APLTestThread(Thread):
	def run(self):
		config = os.path.normpath(os.path.join(here,'..', '..', '..', 'unittest.yaml'))
		try:
			runner.main(config, 'airportlocker.main', False)
		except: # let this fail cleanly when the tests finish
			pass

def wait_for_http(url):
	h = httplib2.Http()
	for t in range(50):
		resp, content = h.request(url)
		if resp.status == 200:
			break
		time.sleep(.5)

class TestBasicClient(object):

	def setup_class(self):
		self.proc = APLTestThread()
		self.proc.start()
		# cherrypy started
		wait_for_occupied_port('localhost', 8090)

		# fab templates loaded and other stuff ready
		wait_for_http('http://localhost:8090/_dev/')
		
		self.base_url = 'http://localhost:8090/'
		self.browser = FabBrowser()

	def teardown_class(self):
		del self.proc

	def test_upload_file(self):
		client = AirportLockerClient(self.base_url, httplib2.Http())
		test_file = os.path.join(here, 'upload_test_file.txt')
		result = client.create(test_file, {'foo': 'bar'})
		print result		
		assert result
		remote_file = client.read(result['value'])
		assert remote_file
		assert remote_file == open(test_file, 'r').read()
		assert False

		
