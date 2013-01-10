from bson import json_util as json

import yg.launch.config

# default config values
config = yg.launch.config.ConfigDict(
    airportlocker_port = 8090,
    production = False,
    docset = 'luggage',

    # mongodb store
    storage_uri = 'mongodb://localhost/airportlocker',

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

_default_config = yg.launch.config.ConfigDict(config)
"A copy of the default config"
