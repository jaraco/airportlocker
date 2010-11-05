import pymongo
import airportlocker
from airportlocker.etc.conf import *

import fab
fab.config['base'] = BASE

import eggmonster 
from eggmonster import env

eggmonster.load_default_yaml(file=os.path.join(BASE, 'etc', 'baseconf.yaml'))
if not eggmonster.managed_env():
	eggmonster.load_local_yaml(file=os.path.normpath(os.path.join(BASE, 'devel.yaml')))

from cherrypy._cplogging import logfmt
from eggmonster import EggmonsterLogHandler
import logging

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

if not os.path.isdir(env.filestore):
	os.makedirs(env.filestore)

airportlocker.store = pymongo.Connection(env.mongo_host,
	env.mongo_port)[env.mongo_db_name]
from airportlocker import migration
attach_eggmonster_handler(migration.log.name)
migration.from_faststore()
