import logging
import importlib
import threading

import yg.mongodb
import path

import airportlocker

# set the level for the root logger so DEBUG and INFO messages for all loggers
#  are allowed to the various handlers.
logging.root.level = logging.DEBUG

def _get_storage_class():
    """
    storage_class, if given in the config, should indicate the class to be
    used.
    """
    spec = airportlocker.config.get('storage_class',
        'airportlocker.lib.filesystem:FileStorage')
    if not spec.startswith('airportlocker.lib.'):
        spec = 'airportlocker.lib.' + spec
    module_name, factory_exp = spec.split(':')
    module = importlib.import_module(module_name)
    factory = eval(factory_exp, module.__dict__)
    return factory

logging.getLogger('airportlocker').info('starting')

# ensure filestore is created as a path.path object.
if airportlocker.config.get('filestore', None):
    airportlocker.config.update(
        filestore = path.path(airportlocker.config.filestore))

airportlocker.storage_class = _get_storage_class()
airportlocker.storage_class.startup()
airportlocker.store = yg.mongodb.connect_db(airportlocker.config.storage_uri,
    default_db_name='airportlocker')
