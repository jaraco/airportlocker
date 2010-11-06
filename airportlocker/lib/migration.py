"""
Routines to migrate from previous versions of airportlocker.
"""

from pmxtools.timing import Stopwatch

import airportlocker
json = airportlocker.json

import logging
log = logging.getLogger(__name__)

def from_faststore():
	"""
	Migrate data from an airportlocker 0.7.x faststore
	Requires that the fs_host, fs_port are still defined and that env.docset
	is the same in the new mongodb as in the old faststore.
	
	Assumes faststore 0.8 was installed by a previous install of
	airportlocker in this Python environment (or manually).
	"""
	from eggmonster import env
	has_faststore_config = hasattr(env, 'fs_host') and hasattr(env, 'fs_port')
	if not has_faststore_config:
		# if the faststore config has been removed, assume no migration
		#  is necessary
		return
	import pkg_resources
	pkg_resources.require('faststore==0.8')
	from faststore.client import FastStoreClient
	log.info('FastStore configuration found - migrating records')
	source = FastStoreClient(env.fs_host, env.fs_port)
	dest = airportlocker.store[env.docset]
	source_keys = set(
		key for key in source.keys(env.docset)
		if not key.startswith('__view__')
		)
	dest_keys = set(rec['_id'] for rec in dest.find())
	missing = source_keys - dest_keys
	if not missing:
		log.info('No records in source not in dest - nothing to migrate.')
		log.info('Consider removing fs_host and fs_port config')
		return
	log.info('Migrating %d records', len(missing))
	elapsed = Stopwatch()
	for key in missing:
		log.debug('Migrating %s', key)
		try:
			dest.insert(json.loads(source.retr(env.docset, key)))
		except Exception:
			log.error("Unhandled exception migrating %s", key)
	log.info('Migration of %d records completed in %s.', len(missing),
		elapsed.split())

def do_local_faststore_migration():
	from eggmonster import env
	env.fs_host = 'mongodb01.g.yougov.local'
	env.fs_port = 10104
	env.docset = 'luggage'
	logging.basicConfig(level=logging.DEBUG)
	import pymongo
	airportlocker.store = pymongo.Connection()['airportlocker']
	from_faststore()
	