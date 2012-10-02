import logging
import importlib

import pymongo

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

def _do_migration():
	storage = airportlocker.storage_class()
	if hasattr(storage, 'migrate'):
		params = airportlocker.config.get('migrate_params', {})
		storage.migrate(**params)

logging.getLogger('airportlocker').info('starting')

airportlocker.storage_class = _get_storage_class()
airportlocker.storage_class.startup()
airportlocker.store = pymongo.Connection(
	airportlocker.config.mongo_host,
	airportlocker.config.mongo_port
	)[airportlocker.config.mongo_db_name]

_do_migration()
