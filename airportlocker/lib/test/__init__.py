import importlib
import os
import time

import cherrypy._cpserver
import pkg_resources
import requests
import yg.launch.config
from fab.testing import FabBrowser

import airportlocker
import airportlocker.control.root

here = os.path.abspath(os.path.dirname(__file__))


def embed_server():
    config_stream = pkg_resources.resource_stream(
        'airportlocker.lib', 'test/config.yaml')
    airportlocker.config.update(
        yg.launch.config.ConfigDict.from_yaml_stream(config_stream))
    importlib.import_module('airportlocker.etc.startup')
    airportlocker.control.root.start()


def wait_for_http(url):
    for t in range(50):
        try:
            requests.get(url)
            return
        except Exception:
            pass
        time.sleep(.5)
    raise RuntimeError("Unable to connect: %s" % url)


class AirportlockerTest(object):
    test_filename = 'upload_test_file.txt'
    test_file = os.path.join(here, test_filename)

    def setup_class(self):
        embed_server()
        airportlocker.database.client.drop_database(airportlocker.database)
        # cherrypy started
        cherrypy._cpserver.wait_for_occupied_port('localhost', 8090)

        # fab templates loaded and other stuff ready
        wait_for_http('http://localhost:8090/_dev/')

        self.base_url = 'http://localhost:8090/'
        self.browser = FabBrowser()

    def teardown_class(self):
        cherrypy.engine.exit()
