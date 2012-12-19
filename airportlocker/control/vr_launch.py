import getopt
import importlib
import logging
import sys

import os
import yaml

import airportlocker
from airportlocker.control import root


def setup_logging():
    logging.basicConfig(level=logging.INFO)

def run():
    if 'APP_SETTINGS_YAML' in os.environ:
        with open(os.environ['APP_SETTINGS_YAML']) as config_stream:
            airportlocker.config.update(yaml.load(config_stream))
    else:
        try:
            opts, args = getopt.getopt(sys.argv[1:],
                                       'c', ['config='])
        except getopt.GetoptError as err:
            print str(err)
            sys.exit(2)
        for o, a in opts:
            if o in ('-c', '--config'):
                with open(a) as config_stream:
                    airportlocker.config.update(
                            yaml.load(config_stream))
    airportlocker.config['airportlocker_port'] = int(os.environ['PORT'])
    setup_logging()
    importlib.import_module('airportlocker.etc.startup')
    root.run()

if __name__ == '__main__':
    run()
