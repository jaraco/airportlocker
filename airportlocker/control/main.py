from __future__ import with_statement

import os
import posixpath

import fab
import cherrypy

import airportlocker
from airportlocker import json
from airportlocker.control.base import Resource, HtmlResource, post
from airportlocker.lib.storage import NotFoundError

def success(value):
    return json.dumps({'status': 'success', 'value': value})

def failure(message):
    return json.dumps({'status': 'failure', 'reason': message})

def items(field_storage):
    """
    Like dict.items, but for cgi.FieldStorage
    """
    for key in field_storage.keys():
        yield key, field_storage.getvalue(key)

def add_extra_metadata(row):
    row['url'] = '/static/%(_id)s' % row

    if row['filename'].startswith('/'):
        row['name_url'] = '/static%(filename)s' % row
        row['cached_url'] = '/cached/%(md5)s%(filename)s' % row
    else:
        row['name_url'] = '/static/%(filename)s' % row
        row['cached_url'] = '/cached/%(md5)s/%(filename)s' % row

    if 'shortname' not in row:
        row['shortname'] = row['filename'].split('/')[-1]

    row['_id'] = str(row['_id'])
    return row

class BasicUpload(HtmlResource):
    template = fab.template('base.tmpl')
    body = fab.template('basicform.tmpl')
    def GET(self, page, *args, **kw):
        cherrypy.response.headers['Content-Type'] = 'application/xhtml+xml'
        page.args = kw


class ListResources(Resource, airportlocker.storage_class):
    def GET(self, page, **kw):
        cherrypy.response.headers['Cache-Control'] = 'no-cache'
        # traditionally, q must be __all to query all. Now that's the default
        #  behavior if no kw is passed... but support it for compatibility.
        kw.pop('q', None)
        if kw:
            res = self._query(**kw)
        else:
            res = self._list()
        return json.dumps(res)

    def _list(self):
        return map(add_extra_metadata, self.find())

    def _query(self, **kw):
        """ Return all records that match the query. """
        return map(add_extra_metadata, self.find(kw))

class ViewResource(Resource, airportlocker.storage_class):
    def GET(self, page, id):
        results = self.find_one(self.by_id(id))
        if not results:
            raise cherrypy.NotFound()
        return json.dumps(results)

class ReadResource(Resource, airportlocker.storage_class):
    def GET(self, page, *args, **kw):
        if not args:
            raise cherrypy.NotFound()
        path = '/'.join(args)
        cherrypy.response.headers['Connection'] = 'close'
        return self.return_file(path)

    def HEAD(self, page, *args, **kw):
        path = '/'.join(args)
        cherrypy.response.headers['Connection'] = 'close'
        return self.head_file(path)

    def return_file(self, path):
        try:
            resource, ct = self.get_resource(path)
        except NotFoundError:
            raise cherrypy.NotFound()
        cherrypy.response.headers.update({
            'Content-Type': ct or 'text/plain',
        })
        return resource

    def head_file(self, path):
        try:
            resource, ct = self.get_resource(path)
        except NotFoundError:
            raise cherrypy.NotFound()
        size = sum([len(l) for l in resource])
        cherrypy.response.headers.update({
            'Content-Type': ct or 'text/plain',
            'Content-Length': size,
        })
        return

class CachedResource(Resource, airportlocker.storage_class):
    """ Expose for CDNed MD5 version, we use /MD5/Filename as url, Filename can be /SurveyName/Filename
    """
    def GET(self, page, *args, **kw):
        if not args:
            raise cherrypy.NotFound()
        if len(args) < 2:
            raise cherrypy.NotFound()
        found_file = None
        path = '/'.join(args[1:])
        if self.fs.exists(filename=path):
            found_file = self.fs.get_last_version(path)
        elif not path.startswith('/') and self.fs.exists(filename='/' + path):
            path = '/' + path
            found_file = self.fs.get_last_version(path)
        if found_file is not None:
            if found_file._file['md5'] == args[0]:
                resource, ct = self.get_resource(path)
                cherrypy.response.headers.update({
                    'Content-Type': ct or 'text/plain',
                    })
                return resource
        raise cherrypy.NotFound()

class CreateOrReplaceResource(Resource, airportlocker.storage_class):
    """
    New endpoint, determine if the incoming file already exists, if it does
    then replace it, if it doesn't then create a new one.
    """
    @post
    def POST(self, page, fields):
        print "YEASGASFASDFASF"
        fields_valid = '_lockerfile' in fields
        if not fields_valid:
            return failure('A  "_lockerfile" is required.')

        # cast fields to a dict here because CGIFieldStorage doesn't have
        # a pop attribute. Also we can't pass FieldStorage to posixpath
        # later so use it's value if it is there.
        prefix = fields['_prefix'].value if '_prefix' in fields else ''

        stream = fields['_lockerfile'].file
        content_type = fields['_lockerfile'].type

        # use override name field if supplied, else use source filename
        name = (fields['name'].value
                if 'name' in fields else fields['_lockerfile'].filename)
        # but always trust the original filename for the extension
        name = self._ensure_extension(name, fields['_lockerfile'].filename)

        filepath = posixpath.join(prefix, name)
        # metadata are all fields that don't begin with '_'
        meta = dict(
            (k, v) for k, v in items(fields)
                if not k.startswith('_')
        )
        # Preserve original filename as a shortname
        meta['shortname'] = fields['_lockerfile'].filename

        current_files = self.find({'filename': filepath}).sort('date')
        if current_files.count():
            latest = current_files[0]
            object_id = str(latest['_id'])
            new_doc = self.update(object_id, meta, stream, content_type)
            return success({'updated': json.dumps(new_doc)})


        oid = self.save(stream, filepath, content_type, meta)
        new_doc = self.find_one(self.by_id(oid))
        return success({'created': json.dumps(new_doc)})

class CreateResource(Resource, airportlocker.storage_class):
    """
    Save the file and make sure the filename is as close as possible to the
    original while still being unique.
    """

    @post
    def POST(self, page, fields):
        '''Save the file to storage'''
        fields_valid = '_new' in fields and '_lockerfile' in fields
        if not fields_valid:
            return failure('A "_new" and "_lockerfile" are required to '
                'create a new document.')

        # cast fields to a dict here because CGIFieldStorage doesn't have
        # a pop attribute. Also we can't pass FieldStorage to posixpath
        # later so use it's value if it is there.
        prefix = fields['_prefix'].value if '_prefix' in fields else ''

        stream = fields['_lockerfile'].file
        content_type = fields['_lockerfile'].type

        # use override name field if supplied, else use source filename
        name = (fields['name'].value
            if 'name' in fields else fields['_lockerfile'].filename)
        # but always trust the original filename for the extension
        name = self._ensure_extension(name, fields['_lockerfile'].filename)
        filepath = posixpath.join(prefix, name)

        # metadata are all fields that don't begin with '_'
        meta = dict(
            (k, v) for k, v in items(fields)
            if not k.startswith('_')
        )
        # Preserve original filename as a shortname
        meta['shortname'] = fields['_lockerfile'].filename

        oid = self.save(stream, filepath, content_type, meta)
        return success(oid)

class UpdateResource(Resource, airportlocker.storage_class):

    @post
    def PUT(self, page, fields, id):
        file_ob = fields.get('_lockerfile', None)
        params = dict(
            stream = file_ob.file,
            content_type = file_ob.type,
        ) if file_ob else dict()

        # metadata are all fields that don't begin with '_'
        meta = dict(
            (k, v) for k, v in items(fields)
            if not k.startswith('_')
        )

        try:
            new_doc = self.update(id, meta=meta, **params)
        except NotFoundError:
            raise cherrypy.NotFound()

        return success({'updated': json.dumps(new_doc)})

class DeleteResource(Resource, airportlocker.storage_class):
    def DELETE(self, page, id):
        return success({'deleted': self.delete(id)})
