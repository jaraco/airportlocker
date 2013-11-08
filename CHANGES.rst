Changes
=======

6.0
---

Dropped support for VR1. Now uses heroku build pack on VR2.

5.3
---

Make max upload size configurable though ``upload_limit`` config parameter.
Default remains 100MB.

5.2
---

Cache resolved CloudFront distributions.

5.0
---

Airportlocker client no longer accepts a custom session object.

4.0
---

Airportlocker client now uses requests instead of httplib2. Clients must
account for the following changes:

 - AirportLockerClient no longer takes an 'h' parameter in the constructor,
   though it does take an optional 'session' parameter, which should be a
   requests.Session instance.
 - AirportLockerClient.create no longer return raw error responses, but
   instead allows request Exceptions to be raised for error responses.
 - AirportLockerClient.exists no longer accepts `None` as a parameter for
   `prefix`.
 - The default behavior is now not to cache locally on disk. If a local,
   disk-based cache is desired, one should pass a suitably-configured
   `session`.

3.0
---

Config no longer accepts mongo_* keys. Use `storage_uri` to indicate the
storage database.

Removed file system support, including migration support.

Renamed `airportlocker.store` to `airportlocker.database`.

2.0
---

The upload module has been revamped to provide a much simpler interface for
uploading multiple files to airportlocker (for Gryphon-specific usage).
Otherwise, the library remains completely backwards-compatible.

1.9
---

Added three new config options needed to sign public urls using an amazon
cloudfront instance (which is automatically created):

aws_keypairid
aws_privatekey
aws_signature_ttl

Check dev_vr.yaml for the default values.

1.0
---

The version was bumped to 1.0 to indicate the backward incompatibility in the
removed faststore migration. The application should otherwise be
backward-compatible with all 0.x versions (or at least recent ones).

* Faststore migration removed.
* Completed implementation of GridFS backend. Enable by adding to the config::

    storage_class: airportlocker.lib.gridfs:GridFSStorage

0.11
----

* Added support for Velociraptor-based deployment.
* Removed dependency on pmxtools.
