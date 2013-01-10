import logging

import yg.mongodb

import airportlocker

def setup_logging():
    # set the level for the root logger so DEBUG and INFO messages for all loggers
    #  are allowed to the various handlers.
    logging.root.level = logging.DEBUG
    logging.getLogger('airportlocker').info('starting')

def setup_storage():
    airportlocker.database = yg.mongodb.connect_db(
        airportlocker.config.storage_uri, default_db_name='airportlocker')

setup_logging()
setup_storage()
