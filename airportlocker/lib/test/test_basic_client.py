import os
import time
import importlib

import httplib2
import pkg_resources
import cherrypy._cpserver
from fab.testing import FabBrowser
import yg.launch.config

import airportlocker.control.root
from airportlocker.lib.client import AirportLockerClient

here = os.path.abspath(os.path.dirname(__file__))

def embed_server():
    config_stream = pkg_resources.resource_stream(
        'airportlocker.lib', 'test/config.yaml')
    airportlocker.config.update(
        yg.launch.config.ConfigDict.from_yaml_stream(config_stream))
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
        raise RuntimeError("Unable to connect: %s" % url)

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
