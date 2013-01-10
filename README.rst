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

When you upload videos and transcoding is activated we use zencoder to run
the transcoding jobs. When running in production zencoder will do a POST to a
public URL that will give airportlocker additional data about the output files.
When running locally for testing we don't have a public facing url so we must
use a fetcher that will periodically ask for our jobs status and when one
finishes it will post to the localhost or dev-vm URL. Zencoder mantains a good
fetcher (in ruby). To install and use:

gem install zencoder-fetcher


To run it you should use:

zencoder_fetcher -u http://localhost:5600/_zencoder/ -l -m 1 06f15509882cc8afb0565af79a9206e1


The -u points to the url where the fetcher will post the information. Note that
needs to change when running on a different machine like a dev-vm.
The -l option tells the fetcher to run in a loop.
The -m 1 tells the fetcher to ignore notifications older than 1 minute ago.
The last parameter is the zencoder API key, it must be the same as your
airportlocker deployment is using.