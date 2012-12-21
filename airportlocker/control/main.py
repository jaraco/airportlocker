from __future__ import with_statement

import os
import posixpath
import time
from urlparse import urljoin

from boto.cloudfront import CloudFrontConnection
from boto.cloudfront.origin import CustomOrigin, S3Origin
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import cherrypy
import fab
import zencoder

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
    apl_public_url = airportlocker.config.get('public_url', '')

    if row['filename'].startswith('/'):
        row['name_url'] = urljoin(apl_public_url,
                                  '/static%(filename)s' % row)
        row['cached_url'] = urljoin(apl_public_url,
                                    '/cached/%(md5)s%(filename)s' % row)
    else:
        row['name_url'] = urljoin(apl_public_url,
                                  '/static/%(filename)s' % row)
        row['cached_url'] = urljoin(apl_public_url,
                                    '/cached/%(md5)s/%(filename)s' % row)

    if 'shortname' not in row:
        row['shortname'] = row['filename'].split('/')[-1]

    row['_id'] = str(row['_id'])
    return row


def get_cloudfront_distribution(public_url=None, s3_bucket=None):
    if s3_bucket is not None:
        public_url = "%s.s3.amazonaws.com" % s3_bucket

    distribution = None
    cf = CloudFrontConnection(airportlocker.config.get('aws_accesskey'),
                              airportlocker.config.get('aws_secretkey'))

    for ds in cf.get_all_distributions():
        if ds.origin.dns_name == public_url:
            distribution = ds.get_distribution()
            break

    if distribution is None:
        if s3_bucket:
            origin = S3Origin(public_url)
        else:
            origin = CustomOrigin(public_url)
        distribution = cf.create_distribution(origin=origin, enabled=True,
                                              trusted_signers=["Self"],
                                              comment='Airportlocker')

    return distribution


def sign_url(unsigned_url, distribution, keypair_id, private_key):
    """ Make a expire time and build the cloudfront url. Finally sign it.
    """
    expire = int(time.time()) + 600 # 10 minutes
    unsigned_url = unsigned_url.replace(distribution.config.origin.dns_name,
                                        distribution.domain_name)
    return distribution.create_signed_url(url=unsigned_url,
                                          keypair_id=keypair_id,
                                          expire_time=expire,
                                          private_key_string=private_key)


def is_public(url):
    for elem in ['localhost', '127.0.0.1']:
        if elem in url:
            return False
    return url.endswith('.local')


def add_extra_signed_metadata(row):
    row = add_extra_metadata(row)

    # Check if we have the configs to produce signed urls, if not return the
    # data as it is.
    private_key = airportlocker.config.get('aws_privatekey', '')
    keypair_id = airportlocker.config.get('aws_keypairid', '')
    if not private_key or not keypair_id:
        return row

    public_url = airportlocker.config.get('public_url', '')

    if is_public(public_url):
        distribution = get_cloudfront_distribution(public_url)
        row['signed_url'] = sign_url(row['cached_url'], distribution,
                                     keypair_id, private_key)

    # Check if the file is a video and has zencoder s3 files to sign.
    s3_bucket = airportlocker.config.get('aws_s3_bucket', '')
    if 'zencoder_outputs' in row and s3_bucket:
        distribution = get_cloudfront_distribution(s3_bucket=s3_bucket)
        for output in row['zencoder_outputs']:
            output['signed_url'] = sign_url(output['url'], distribution,
                                            keypair_id, private_key)

    return row


def validate_fields(fields, required=None):
    if required is None:
        required = ["_new", "_lockerfile"]
    for field in required:
        if field not in fields:
            return False
    return True


def extract_fields(fields):
    # cast fields to a dict here because CGIFieldStorage doesn't have
    # a pop attribute. Also we can't pass FieldStorage to posixpath
    # later so use it's value if it is there.
    prefix = fields['_prefix'].value if '_prefix' in fields else ''

    stream = fields['_lockerfile'].file
    content_type = fields['_lockerfile'].type

    # use override name field if supplied, else use source filename
    name = (fields['name'].value
            if 'name' in fields else fields['_lockerfile'].filename)
    return prefix, stream, content_type, name


def prepare_meta(fields):
    meta = dict(
        (k, v) for k, v in items(fields)
        if not k.startswith('_')
    )
    # Preserve original filename as a shortname
    if '_lockerfile' in fields:
        meta['shortname'] = fields['_lockerfile'].filename

    return meta


def send_to_zencoder(s3filename):
    """ Prepare the job input and send it out to zencoder for the
    transcoding magic.
    """
    zen = zencoder.Zencoder(airportlocker.config.get('zencoder_api_key'))
    bucket = airportlocker.config.get('aws_s3_bucket')

    notification_url = airportlocker.config.get('zencoder_notification_url',
                                                None)
    if 'localhost' in notification_url or not notification_url:
        # This is the test url that zencoder uses see, if not there will be no
        # notifications for zencoder-fetcher. See readme.
        notification_url = 'http://zencoderfetcher/'

    notification = [{'format': 'json',
                     'url': notification_url}]

    outputs = []
    for output in airportlocker.config.get('zencoder_outputs'):
        extension = output['extension']
        suffix = str(output['suffix'])
        filename, source_ext = os.path.splitext(s3filename)
        output_url = 's3://' + bucket + '/' + filename + '_' + suffix + '.' + \
                     extension
        output.update({'url': output_url, "public": True})
        # We don't want to pass this params to zencoder since they are internal
        # only.
        del output['extension']
        del output['suffix']

        if notification is not None:
            output.update({'notifications': notification})

        outputs.append(output)

    job = zen.job.create('s3://' + airportlocker.config.get('aws_s3_bucket') +
                         '/' + s3filename, outputs)

    if job.code == 201:
        # Save the info about the outputs
        return job.body

    return None


def upload_to_s3(filename, content, content_type):
    """ Upload to s3. Beware of the leading / in the filename.
    """
    conn = S3Connection(airportlocker.config.get('aws_accesskey'),
                        airportlocker.config.get('aws_secretkey'))
    bucket = conn.get_bucket(airportlocker.config.get('aws_s3_bucket'))
    k = Key(bucket)
    k.key = filename.lstrip('/')
    k.set_metadata("Content-Type", content_type)
    k.set_contents_from_file(content)
    k.set_acl('public-read')
    return k.key


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
        """ Return all records that match the query. We remove """
        if '_prefix' in kw:
            kw.pop('_prefix', '')
        return map(add_extra_metadata, self.find(kw))


class ListSignedResources(Resource, airportlocker.storage_class):
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
        return map(add_extra_signed_metadata, self.find())

    def _query(self, **kw):
        """ Return all records that match the query. """
        return map(add_extra_signed_metadata, self.find(kw))


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


class ZencoderResource(Resource, airportlocker.storage_class):
    """ Notification endpoint for Zencoder to post the results of a job and
    output meta information.
    """

    def POST(self, page):
        """ Zencoder POSTs data here.
        """
        if self.is_json():
            cherrypy.request.body.process()
            rawbody = cherrypy.request.body.read()
            body = json.loads(rawbody)
            job_id = body['job']['id']
            file_meta = self.find_one({'zencoder_job_id': job_id})
            if not file_meta:
                raise cherrypy.NotFound()
            for output in file_meta['zencoder_outputs']:
                if output['id'] == body['output']['id']:
                    output.update(body['output'])
                    result = self.coll.files.update({'_id': file_meta['_id'],
                        'zencoder_outputs.id': output['id']},
                        {'$set': {"zencoder_outputs.$": output}})
                    return success('Updated')

        raise cherrypy.NotFound()


class CachedResource(Resource, airportlocker.storage_class):
    """ Expose for CDNed MD5 version, we use /MD5/Filename as url,
    Filename can be /SurveyName/Filename
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
    """ New endpoint, determine if the incoming file already exists, if it does
    then replace it, if it doesn't then create a new one.
    """
    @post
    def POST(self, page, fields):
        if not validate_fields(fields, ["_lockerfile", ]):
            return failure('A "_lockerfile" is required.')

        prefix, stream, content_type, name = extract_fields(fields)

        # but always trust the original filename for the extension
        name = self._ensure_extension(name, fields['_lockerfile'].filename)
        file_path = posixpath.join(prefix, name)

        meta = prepare_meta(fields)

        current_files = self.find({'filename': file_path}).sort('date')
        updated = False

        if current_files.count():
            object_id = str(current_files[0]['_id'])
            new_doc = self.update(object_id, meta, stream, content_type,
                overwrite=True)
            object_id = str(new_doc['_id'])
            updated = True
        else:
            object_id = self.save(stream, file_path, content_type, meta,
                            overwrite=True)
            new_doc = self.find_one(self.by_id(object_id))

        if 'video' in content_type:
            resource, ct = self.get_resource(file_path)
            s3_file = upload_to_s3(file_path, resource, ct)
            job = send_to_zencoder(s3_file)
            meta['zencoder_job_id'] = job['id']
            meta['zencoder_outputs'] = job['outputs']
            new_doc = self.update(object_id, meta)

        if updated:
            return success({'updated': json.dumps(new_doc)})

        return success({'created': json.dumps(new_doc)})


class CreateResource(Resource, airportlocker.storage_class):
    """
    Save the file and make sure the filename is as close as possible to the
    original while still being unique.
    """
    @post
    def POST(self, page, fields):
        if not validate_fields(fields):
            return failure('A "_new" and "_lockerfile" are required to '
                'create a new document.')

        prefix, stream, content_type, name = extract_fields(fields)
        # but always trust the original filename for the extension
        name = self._ensure_extension(name, fields['_lockerfile'].filename)
        file_path = posixpath.join(prefix, name)

        meta = prepare_meta(fields)

        oid = self.save(stream, file_path, content_type, meta)
        return success(oid)


class UpdateResource(Resource, airportlocker.storage_class):

    @post
    def PUT(self, page, fields, id):
        file_ob = fields.get('_lockerfile', None)
        params = dict(
            stream = file_ob.file,
            content_type = file_ob.type,
        ) if file_ob else dict()

        meta = prepare_meta(fields)

        try:
            new_doc = self.update(id, meta=meta, **params)
        except NotFoundError:
            raise cherrypy.NotFound()

        return success({'updated': json.dumps(new_doc)})


class DeleteResource(Resource, airportlocker.storage_class):
    def DELETE(self, page, id):
        return success({'deleted': self.delete(id)})
