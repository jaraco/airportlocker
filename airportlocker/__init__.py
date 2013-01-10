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

    # Integration only zencoder api key. Use a commercial key in production
    #  to support longer videos.
    zencoder_api_key = '06f15509882cc8afb0565af79a9206e1',
    zencoder_outputs = [
        {
            'label': 'HTML5/Flash/MP4/H.264', 'h264_profile': 'high',
            'extension': 'mp4', 'suffix': 'html5_mp4',
        },
        {
            'label': 'HTML5/WebM', 'extension': 'webm',
            'suffix': 'html5_webm',
        },
        {'label': 'HTML5/Ogg', 'extension': 'ogg', 'suffix': 'html5_ogg',},
        {
            'label': 'Mobile/3GP/MPEG4 non-smartphones', 'size': '320x240',
            'extension': '3gp', 'suffix': 'mov_3gp',
        },
    ],

)

_default_config = yg.launch.config.ConfigDict(config)
"A copy of the default config"
