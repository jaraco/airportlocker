Changes
=======

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
