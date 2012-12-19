import importlib
import logging
import os

import yg.launch.cmdline

import airportlocker
from airportlocker.control import root


def setup_logging():
    logging.basicConfig(level=logging.INFO)

def run():
    airportlocker.config.update(
        yg.launch.cmdline.get_parser().parse_args().config)
    airportlocker.config['airportlocker_port'] = int(os.environ['PORT'])
    setup_logging()
    importlib.import_module('airportlocker.etc.startup')
    root.run()

if __name__ == '__main__':
    run()
