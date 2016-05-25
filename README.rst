.. -*- restructuredtext -*-

airportlocker
=============

Media resource storage for YouGov apps. Uses MongoDB for storage of metadata
and provides two backends for configurable storage of the file payload (either
in MongoDB or on the filesystem).

Stores all media with versions where the resource URI is unchanging for
a given resource.

You can consume the API using XMLHttpRequest since we include Access-Control-Allow headers.


Running airportlocker
---------------------

Clone the repo, and install/update the requirements:

pip install -U . -i http://cheese.yougov.net

To run a dev airporlocker instance you can do it with using the
velociraptor runer and the config at the root of your repo checkout like this:

PORT=5600 python -m airportlocker.control.vr_launch --config=configs/dev_vr.yaml

The service will be running at:

http://localhost:5600


Uploading videos
----------------

When uploading videos and if transcoding is activated, APL uses Zencoder to run
the transcoding jobs. When running in production, Zencoder
will do a POST to a supplied webhook
URL no signal airportlocker about the job status and output.
When running locally for testing, most developers don't have
a routable IP address, so we rely on
a `fetcher <https://github.com/zencoder/zencoder-fetcher>`_ that
will periodically query job status, and when one
finishes, it will post to the indicated APL URL. Zencoder
mantains a good
fetcher (in ruby). To install and use:

gem install zencoder-fetcher


To run it you should use::

    zencoder_fetcher --url $AIRPORTLOCKER_URL/_zencoder/ --loop --since 1 $API_KEY


The $API_KEY must be the same as the key used by airportlocker to submit
the jobs.
