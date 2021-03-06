from __future__ import absolute_import, unicode_literals

import os

import gridfs

from . import storage


def get_resource_uri(row):
    """
    Return the URI for the given GridFS resource.

    Resource URIs have the form: '<file md5>/<oid>.<file extension>'
    """
    extension = os.path.splitext(row['filename'])[1]
    return '{}/{}{}'.format(row['md5'], row['_id'], extension)


class GridFSStorage(storage.Storage):
    """
    A mix-in class to be used with Resource controller objects providing
    gridfs-backed resource file storage.
    """

    def find(self, *args, **kwargs):
        return self.coll.files.find(*args, **kwargs)

    def find_one(self, *args, **kwargs):
        return self.coll.files.find_one(*args, **kwargs)

    @property
    def fs(self):
        return gridfs.GridFS(self.coll.database, self.coll.name)

    def verified_filename(self, fn):
        """
        Return a unique, human-readable filename that's safe to save.
        """
        return storage.unique_name(storage.numbered_files(fn), self.exists)

    def exists(self, filepath):
        """
        Return True if filepath already exists in the filestore.
        """
        return self.fs.exists(filename=filepath)

    def save(self, stream, filepath, content_type, meta, overwrite=False):
        if not overwrite:
            filepath = self.verified_filename(filepath)
        return self.fs.put(stream, filename=filepath,
            content_type=content_type, **meta)

    @staticmethod
    def _ensure_extension(name, orig_name):
        # just return the original name - no override needed for GridFS
        # storage
        return name

    def update(self, id, meta, stream=None, content_type=None, overwrite=False):
        """
        Update the document identified by id with the new metadata and file
        stream (if supplied).
        Return the updated metadata.
        """
        if not self.fs.exists(self.by_id(id)):
            raise storage.NotFoundError(id)

        if stream:
            if not content_type:
                raise ValueError("You can't update the stream without "
                    "specifying the content type.")
            return self.replace_file(id, stream, content_type, meta, overwrite)

        spec = dict(_id=self.by_id(id))
        self.coll.files.update(spec, {"$set": meta})
        new_doc = self.find_one(self.by_id(id))
        return new_doc

    def replace_file(self, id, stream, content_type, meta, overwrite=False):
        """
        GridFS doesn't easily enable overriding an existing file, so do
        the work here. id must exist.

        Saves the new file, removes the old file.

        Return the newly-created doc (which will have a new id).

        This behavior was created to match the FileStorage implementation.
        Consider re-defining the meaning of .update to be more
        straightforward.
        """
        orig_meta = self.find_one(self.by_id(id))
        filepath = orig_meta['filename']

        # preserve original resource class and signature ttl, if not overridden
        if 'class' in orig_meta:
            meta.setdefault('class', orig_meta['class'])
        if 'ttl' in orig_meta:
            meta.setdefault('ttl', orig_meta['ttl'])

        new_id = self.save(stream, filepath, content_type, meta, overwrite)
        self.delete(id)
        return self.fs.get(self.by_id(new_id))._file

    def get_resource(self, key):
        """
        Retrieve a resource by key (file path or unique ID).
        Returns the document stream and content type.
        """
        if self.fs.exists(filename=key):
            file = self.fs.get_last_version(key)
        elif self.fs.exists(self.by_id(key)):
            file = self.fs.get(self.by_id(key))
        else:
            raise storage.NotFoundError(key)
        return file, file.content_type

    def delete(self, id):
        """
        Delete the file indicated by id. Return the metadata for the deleted
        document or an empty dict if the id did not exist.
        """
        try:
            id = self.by_id(id)
            meta = self.fs.get(id)._file
            self.fs.delete(id)
        except gridfs.errors.NoFile:
            return {}
        return meta
