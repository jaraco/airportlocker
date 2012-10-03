
# prefer simplejson to json, but fallback to json
try:
	import simplejson as json
except ImportError:
	import json

from jaraco.util.dictlib import ItemsAsAttributes

class ConfigDict(ItemsAsAttributes, dict):
	"A dictionary that provides items as attributes"

# default config values
config = ConfigDict(
	airportlocker_port = 8090,
	production = False,
	docset = 'luggage',

	# file storage
	storage_class = 'airportlocker.lib.filesystem:FileStorage',
	filestore = 'file_storage',

	# mongodb store
	mongo_host = 'localhost',
	mongo_port = 27017,
	mongo_db_name = 'airportlocker',

	# performance tweaks (necessary for static file serving)
	threads = 30,

	# error emails
	email_error = False,
	email_list = [],
	email_server = 'vemail1',

	# Logging to eggmonster
	eggmonster_error = False,
	eggmonster_access = False,

	log_host = "vesyslogd",
	log_port = 13000,
	log_facility = "airportlocker",
)
