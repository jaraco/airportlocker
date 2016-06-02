import importlib
import logging
import os

import yg.launch.cmdline
import yg.newrelic
import cherrypy

import airportlocker
from airportlocker.control import root


def setup_logging():
    logging.basicConfig(level=logging.INFO)

    # prevent CherryPy messages from being logged twice
    cherrypy.log.error_log.propagate = False
    cherrypy.log.access_log.propagate = False


def initialize_newrelic():
    key = airportlocker.config.get('newrelic_license_key')
    if not key:
        return

    app_name = airportlocker.config.get('newrelic_app_name', 'Airportlocker')
    conf = airportlocker.config.get('newrelic', {})
    yg.newrelic.initialize(app_name, key, conf, environment="Production")


def run():
    conf = yg.launch.cmdline.get_parser().parse_args().config
    airportlocker.config.update(conf)
    airportlocker.config['airportlocker_port'] = int(os.environ['PORT'])
    initialize_newrelic()
    setup_logging()
    importlib.import_module('airportlocker.etc.startup')
    root.run()

if __name__ == '__main__':
    run()
