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

def _build_uri_from_legacy_config():
    """
    Prior to airportlocker 1.8, config could be specified using these keys:
      - mongo_host
      - mongo_port
      - mongo_db_name

    If any of those parameters are present, construct the storage_uri from
    those parameters (and their former defaults).
    """
    legacy_keys = 'mongo_host', 'mongo_port', 'mongo_db_name'
    if not any(key in airportlocker.config for key in legacy_keys):
        return
    host = airportlocker.config.get('mongo_host', 'localhost')
    port = airportlocker.config.get('mongo_port', 27017)
    if port != 27017:
        host += ':{port}'.format(port=port)
    db_name = airportlocker.config.get('mongo_db_name', 'airportlocker')
    airportlocker.config['storage_uri'] = 'mongodb://{host}/{db_name}'.format(
        host=host, db_name=db_name)

logging.getLogger('airportlocker').info('starting')

# ensure filestore is created as a path.path object.
if airportlocker.config.get('filestore', None):
    airportlocker.config.update(
        filestore = path.path(airportlocker.config.filestore))

airportlocker.storage_class = _get_storage_class()
airportlocker.storage_class.startup()
_build_uri_from_legacy_config()
airportlocker.store = yg.mongodb.connect_db(airportlocker.config.storage_uri,
    default_db_name='airportlocker')
