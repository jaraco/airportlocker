import os.path
from urlparse import urlparse

import pymongo
import path
from boto.s3.connection import S3Connection

aws_accesskey = '<access_key>'
aws_secretkey = '<secret_key>'
aws_s3_bucket = 'yg-zencoder'


def get_resource_uri(row):
    """
    Return the URI for the given GridFS resource.

    Resource URIs have the form: '<file md5>/<oid>.<file extension>'
    """
    extension = os.path.splitext(row['filename'])[1]
    return '{}{}'.format(get_resource_uri(row), extension)


def get_resource_key(row):
    return '{}/{}'.format(row['md5'], row['_id'])


def force_https(url):
    """Return an HTTPS version of the given URL."""
    if url.startswith('http:'):
        url = url.replace('http:', 'https:', 1)
    return url

s3 = S3Connection(aws_accesskey, aws_secretkey)
bucket = s3.get_bucket(aws_s3_bucket)
print('bucket: {}'.format(bucket))

con = pymongo.MongoClient('mgo11.ldc.yougov.local')
# con = pymongo.MongoClient('vmgo10.paix.yougov.local')
files = con.airportlocker.luggage.files

videos = files.find(
    {
        'contentType': {'$regex': '^video/'},
        'zencoder_outputs.state': 'finished',
    },
)

for file in videos:
    filename = path.path(file['filename'].lstrip('/'))
    # print('contentType: {}'.format(file.get('contentType')))
    src = filename.stripext()
    dst = get_resource_key(file)

    print('src: {}'.format(src))
    print('dst: {}'.format(dst))

    for i, zencoder_file in enumerate(file['zencoder_outputs']):
        old_url = zencoder_file['url']

        if src not in old_url:
            print('Skipping {}'.format(src))
            print('url: {}'.format(old_url))
            print
            continue

        if not old_url.startswith('http://yg-zencoder.s3.amazonaws.com/'):
            raise ValueError(old_url)

        new_url = force_https(old_url).replace(src, dst, 1)

        print('old url: {}'.format(old_url))
        print('new url: {}'.format(new_url))

        src_key = urlparse(old_url).path.lstrip('/')
        dst_key = urlparse(new_url).path.lstrip('/')

        print('src key: {}'.format(src_key))
        print('dst key: {}'.format(dst_key))

        s3_src = bucket.get_key(src_key)
        if s3_src is None:
            raise ValueError(src_key)
        print(s3_src, s3_src.bucket.name, s3_src.key)

        s3_dst = s3_src.copy(bucket.name, dst_key)
        print(s3_dst)
        s3_dst.set_canned_acl('public-read')
        print

        print('_id: {}'.format(file['_id']))
        url_field = 'zencoder_outputs.{}.url'.format(i)
        old_url_field = 'zencoder_outputs.{}.old_url'.format(i)
        update_fields = {url_field: new_url, old_url_field: old_url}
        # print(update_fields)
        print(files.update(
            {'_id': file['_id'], url_field: old_url},
            {'$set': update_fields},
        ))
        print
