import os
import sys
import logging

import pymongo

import airportlocker

# set the level for the root logger so DEBUG and INFO messages for all loggers
#  are allowed to the various handlers.
logging.root.level = logging.DEBUG

def _get_filestore():
	filestore = airportlocker.config.filestore
	filestore = filestore.replace('{prefix}', sys.prefix)
	filestore = filestore.replace('/usr/var', '/var')
	if not os.path.isdir(filestore):
		os.makedirs(filestore)
	return filestore

airportlocker.filestore = _get_filestore()
airportlocker.store = pymongo.Connection(
	airportlocker.config.mongo_host,
	airportlocker.config.mongo_port
	)[airportlocker.config.mongo_db_name]

from airportlocker.lib import migration
migration.from_faststore()
