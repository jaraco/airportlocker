from __future__ import with_statement

from copy import deepcopy
import gc
import os
import posixpath
import time
from urlparse import urljoin, urlparse

from py31compat import functools as functools32

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
from airportlocker.lib.gridfs import GridFSStorage

CSS_MIME_TYPES = ['text/css']
CSV_MIME_TYPES = [
    'application/csv',
    'application/x-csv',
    'text/csv',
    'text/x-comma-separated-values',
]
JAVASCRIPT_MIME_TYPES = [
    'application/javascript',
    'application/x-javascript',
    'text/javascript',
]


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
    apl_public_url = airportlocker.config.get('public_url', '')
    uri = get_resource_uri(row)
    row['url'] = urljoin(apl_public_url, '/internal/{}'.format(uri))

    # old-style URLs (should eventually be deprecated)
    filename = row['filename']
    if not filename.startswith('/'):
        filename = '/' + filename
    row['name_url'] = urljoin(apl_public_url, '/static{}'.format(filename))
    row['cached_url'] = urljoin(apl_public_url,
                                '/cached/{}{}'.format(row['md5'], filename))

    if 'shortname' not in row:
        row['shortname'] = row['filename'].split('/')[-1]

    row['_id'] = str(row['_id'])
    return row


def get_resource_uri(row):
    """
    Return the URI for the given GridFS resource.

    Resource URIs have the form: '<file md5>/<oid>.<file extension>'
    """
    extension = os.path.splitext(row['filename'])[1]
    return '{}/{}{}'.format(row['md5'], row['_id'], extension)


@functools32.lru_cache()
def get_cloudfront_distribution(public_url, is_s3=False):
    distribution = None
    cf = CloudFrontConnection(airportlocker.config.get('aws_accesskey'),
                              airportlocker.config.get('aws_secretkey'))

    rewrite_url = (
        not is_s3 and
        (public_url.startswith('http://') or public_url.startswith('https://'))
    )
    if rewrite_url:
        public_url = urlparse(public_url).netloc

    for ds in cf.get_all_distributions():
        if ds.origin.dns_name == public_url:
            distribution = ds.get_distribution()
            break

    if distribution is None:
        if is_s3:
            origin = S3Origin(public_url)
        else:
            origin = CustomOrigin(public_url)
            origin.origin_protocol_policy = 'match-viewer'
        distribution = cf.create_distribution(origin=origin, enabled=True,
                                              trusted_signers=["Self"],
                                              comment='Airportlocker')

    return distribution


def get_cloudfront_s3_distribution(s3_bucket):
    public_url = "%s.s3.amazonaws.com" % s3_bucket
    return get_cloudfront_distribution(public_url, is_s3=True)


def sign_url(unsigned_url, distribution, keypair_id, private_key):
    """ Make a expire time and build the cloudfront url. Finally sign it.
    """
    signature_ttl = int(airportlocker.config.get('aws_signature_ttl', 600))
    expire = int(time.time()) + signature_ttl
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
    return not url.endswith('.local')


def get_default_resource_class(content_type):
    class_ = 'private'
    if content_type in CSV_MIME_TYPES:
        class_ = 'internal'
    elif content_type in (CSS_MIME_TYPES + JAVASCRIPT_MIME_TYPES):
        class_ = 'public'
    return class_


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

        uri = get_resource_uri(row)
        if row.get('class') == 'public':
            url = urljoin(public_url, '/public/{}'.format(uri))
            row['url'] = url.replace(distribution.config.origin.dns_name,
                                     distribution.domain_name)
        elif row.get('class') == 'private':
            url = urljoin(public_url, '/private/{}'.format(uri))
            row['url'] = sign_url(url, distribution, keypair_id, private_key)

        # old-style URL (should eventually be deprecated)
        row['signed_url'] = sign_url(row['cached_url'], distribution,
                                     keypair_id, private_key)

    # Check if the file is a video and has zencoder s3 files to sign.
    s3_bucket = airportlocker.config.get('aws_s3_bucket', '')
    if 'zencoder_outputs' in row and s3_bucket:
        distribution = get_cloudfront_s3_distribution(s3_bucket)
        for output in row['zencoder_outputs']:
            output['signed_url'] = sign_url(output['url'], distribution,
                                            keypair_id, private_key)
            if row.get('class') == 'private':
                output['url'] = output['signed_url']

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


def get_notification_url():
    notification_url = deepcopy(
        airportlocker.config.get('zencoder_notification_url', None))
    if 'localhost' in notification_url or not notification_url:
        # This is the test url that zencoder uses see, if not there will be no
        # notifications for zencoder-fetcher. See readme.
        notification_url = 'http://zencoderfetcher/'
    return notification_url


def get_output_url(bucket, output, s3filename):
    extension = output['extension']
    suffix = str(output['suffix'])
    filename, source_ext = os.path.splitext(s3filename)
    output_url = 's3://' + bucket + '/' + filename + '_' + suffix + '.' + \
                 extension
    return output_url


def get_outputs(bucket, notification, s3filename):
    outputs = []
    for output in deepcopy(airportlocker.config.get('zencoder_outputs')):
        output.update({'url': get_output_url(bucket, output, s3filename),
                       "public": True, 'notifications': notification})
        # We don't want to pass this params to zencoder since they are internal
        # only.
        del output['extension']
        del output['suffix']
        outputs.append(output)
    return outputs


def send_to_zencoder(s3filename):
    """ Prepare the job input and send it out to zencoder for the
    transcoding magic.
    """
    zen = zencoder.Zencoder(airportlocker.config.get('zencoder_api_key'))
    bucket = airportlocker.config.get('aws_s3_bucket')
    notification = [{'format': 'json', 'url': get_notification_url()}]
    outputs = get_outputs(bucket, notification, s3filename)

    url = 's3://%s/%s' % (
            airportlocker.config.get('aws_s3_bucket'), s3filename)
    job = zen.job.create(input=url, outputs=outputs)

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


class ListResources(Resource, GridFSStorage):
    def GET(self, page, **kw):
        cherrypy.response.headers['Cache-Control'] = 'no-cache'
        # traditionally, q must be __all to query all. Now that's the default
        #  behavior if no kw is passed... but support it for compatibility.
        kw.pop('q', None)
        if kw:
            res = self._query(**kw)
        else:
            res = self._list()

        json_string = json.dumps(res)
        del res
        gc.collect()
        return json_string

    def _list(self):
        return map(add_extra_metadata, self.find())

    def _query(self, **kw):
        """ Return all records that match the query. We remove """
        if '_prefix' in kw:
            kw.pop('_prefix', '')
        return map(add_extra_metadata, self.find(kw))


class ListSignedResources(Resource, GridFSStorage):
    def GET(self, page, **kw):
        cherrypy.response.headers['Cache-Control'] = 'no-cache'
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


class ViewResource(Resource, GridFSStorage):
    def GET(self, page, id):
        results = self.find_one(self.by_id(id))
        if not results:
            raise cherrypy.NotFound()
        return json.dumps(results)


class ReadResource(Resource, GridFSStorage):
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

    def find_file(self, path):
        found_file = None
        if self.fs.exists(filename=path):
            found_file = self.fs.get_last_version(path)
        elif not path.startswith('/') and self.fs.exists(filename='/' + path):
            path = '/' + path
            found_file = self.fs.get_last_version(path)
        return found_file, path

    def return_file(self, path):
        found_file, path = self.find_file(path)
        if found_file is not None:
            try:
                resource, ct = self.get_resource(path)
            except NotFoundError:
                raise cherrypy.NotFound()
            cherrypy.response.headers.update({
                'Content-Type': ct or 'text/plain',
            })
            return resource
        raise cherrypy.NotFound()

    def head_file(self, path):
        found_file, path = self.find_file(path)
        if found_file is not None:
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
        raise cherrypy.NotFound()


class ZencoderResource(Resource, GridFSStorage):
    """ Notification endpoint for Zencoder to post the results of a job and
    output meta information.
    """

    def POST(self, page):
        """ Zencoder POSTs data here.
        """
        if not self.is_json():
            raise cherrypy.NotFound()

        cherrypy.request.body.process()
        rawbody = cherrypy.request.body.read()
        body = json.loads(rawbody)
        job_id = body['job']['id']
        file_meta = self.find_one({'zencoder_job_id': job_id})
        if not file_meta:
            raise cherrypy.NotFound()
        matching_outputs = (
            output for output in file_meta['zencoder_outputs']
            if output['id'] == body['output']['id']
        )
        for output in matching_outputs:
            if 'url' in body['output']:
                body['output']['contentType'] = \
                    self.get_video_content_type(body['output']['url'])
            output.update(body['output'])
            spec = {
                '_id': file_meta['_id'],
                'zencoder_outputs.id': output['id'],
            }
            doc = {
                '$set': {"zencoder_outputs.$": output}
            }
            self.coll.files.update(spec, doc)
            return success('Updated')

    @staticmethod
    def get_video_content_type(url):
        """Return the content type for a video file based on its extension."""
        path = urlparse(url).path
        extension = os.path.splitext(path)[1].lstrip('.')
        return 'video/{}'.format(extension)


class CachedResource(Resource, GridFSStorage):
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


class CreateOrReplaceResource(Resource, GridFSStorage):
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
            meta.setdefault('class', get_default_resource_class(content_type))
            object_id = self.save(stream, file_path, content_type, meta,
                                  overwrite=True)
            new_doc = self.find_one(self.by_id(object_id))

        if 'video' in content_type:
            resource, ct = self.get_resource(file_path)
            filename = get_resource_uri(resource._file)
            s3_file = upload_to_s3(filename, resource, ct)
            job = send_to_zencoder(s3_file)
            meta['zencoder_job_id'] = job['id']
            meta['zencoder_outputs'] = job['outputs']
            new_doc = self.update(object_id, meta)

        if updated:
            return success({'updated': json.dumps(new_doc)})

        return success({'created': json.dumps(new_doc)})


class CreateResource(Resource, GridFSStorage):
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
        if 'class' not in meta:
            meta['class'] = get_default_resource_class(content_type)

        oid = self.save(stream, file_path, content_type, meta)
        return success(oid)


class UpdateResource(Resource, GridFSStorage):
    @post
    def PUT(self, page, fields, id):
        file_ob = fields.get('_lockerfile', None)
        params = dict(
            stream=file_ob.file,
            content_type=file_ob.type,
        ) if file_ob else dict()

        meta = prepare_meta(fields)

        try:
            new_doc = self.update(id, meta=meta, **params)
        except NotFoundError:
            raise cherrypy.NotFound()

        return success({'updated': json.dumps(new_doc)})


class DeleteResource(Resource, GridFSStorage):
    def DELETE(self, page, id):
        return success({'deleted': self.delete(id)})


class GetResource(Resource, GridFSStorage):
    def GET(self, page, md5, file):
        id = os.path.splitext(file)[0]
        try:
            resource, ct = self.get_resource(id)
        except NotFoundError:
            raise cherrypy.NotFound()

        if resource.md5 != md5:
            raise cherrypy.NotFound()

        if not self._validate(resource):
            raise cherrypy.NotFound()

        cherrypy.response.headers.update({
            'Content-Type': ct or 'text/plain',
        })
        return resource

    def _validate(self, resource):
        return resource._file.get('class') == self.resource_class


class GetInternalResource(GetResource):
    resource_class = 'internal'


class GetPrivateResource(GetResource):
    resource_class = 'private'


class GetPublicResource(GetResource):
    resource_class = 'public'
