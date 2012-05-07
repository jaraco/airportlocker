import os
import sys

import pkg_resources
import pymongo
import fab
import eggmonster
from eggmonster import env

import airportlocker

BASE = pkg_resources.resource_filename('airportlocker', '')

fab.config['base'] = BASE

eggmonster.load_default_yaml(file=os.path.join(BASE, 'etc', 'baseconf.yaml'))
if not eggmonster.managed_env():
	eggmonster.load_local_yaml(file=os.path.normpath(os.path.join(BASE, 'devel.yaml')))

from cherrypy._cplogging import logfmt
from eggmonster.log_client import EggmonsterLogHandler
import logging

# set the level for the root logger so DEBUG and INFO messages for all loggers
#  are allowed to the various handlers.
logging.root.level = logging.DEBUG

def attach_eggmonster_handler(log_id):
	log = logging.getLogger(log_id)
	handler = EggmonsterLogHandler(env.log_host, env.log_port, env.log_facility)
	handler.setLevel(logging.DEBUG)
	handler.setFormatter(logfmt)
	log.addHandler(handler)

if env.eggmonster_error:
	attach_eggmonster_handler('cherrypy.error')

if env.eggmonster_access:
	attach_eggmonster_handler('cherrypy.access')

def _get_filestore():
	filestore = env.filestore
	filestore = filestore.replace('{prefix}', sys.prefix)
	filestore = filestore.replace('/usr/var', '/var')
	if not os.path.isdir(filestore):
		os.makedirs(filestore)
	return filestore

airportlocker.filestore = _get_filestore()
airportlocker.store = pymongo.Connection(env.mongo_host,
	env.mongo_port)[env.mongo_db_name]

from airportlocker.lib import migration
attach_eggmonster_handler(migration.log.name)
migration.from_faststore()
