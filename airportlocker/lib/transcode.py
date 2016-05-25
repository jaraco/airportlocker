import os
from copy import deepcopy

import zencoder
from boto.s3.connection import S3Connection
from boto.s3.key import Key

import airportlocker
from airportlocker.lib.gridfs import get_resource_uri


def get_notification_url():
    """
    Get the notification URL to be submitted to Zencoder
    when submitting jobs.
    """
    # Supply a special URL that Zencoder will use
    # to simulate a successful notification. A fetcher
    # must be used to poll for the notification.
    # https://github.com/zencoder/zencoder-fetcher
    fetcher_url = 'http://zencoderfetcher'
    notification_url = airportlocker.config.get(
        'zencoder_notification_url',
        fetcher_url,
    )
    if 'localhost' in notification_url:
        notification_url = fetcher_url
    return notification_url


def get_output_url(bucket, output, s3filename):
    extension = output['extension']
    suffix = str(output['suffix'])
    filename, source_ext = os.path.splitext(s3filename)
    tmpl = 's3://{bucket}/{filename}_{suffix}.{extension}'
    return tmpl.format(**locals())


def get_outputs(bucket, notifications, s3filename):
    """
    Transform the zencoder_outputs config into output
    definitions suitable for passing to zencoder.
    """
    outputs = deepcopy(airportlocker.config.get('zencoder_outputs'))
    for output in outputs:
        output.update(
            url=get_output_url(bucket, output, s3filename),
            public=True,
            notifications=notifications,
        )
        # Omit internal params
        del output['extension']
        del output['suffix']
    return outputs


def send_to_zencoder(s3filename):
    """
    Prepare the job input and send it out to zencoder for
    transcoding.
    """
    zen = zencoder.Zencoder(airportlocker.config.get('zencoder_api_key'))
    bucket = airportlocker.config.get('aws_s3_bucket')
    notifications = [{'format': 'json', 'url': get_notification_url()}]
    outputs = get_outputs(bucket, notifications, s3filename)

    url = 's3://{bucket}/{s3filename}'.format(**locals())
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


def submit(resource, content_type):
    filename = get_resource_uri(resource._file)
    s3_file = upload_to_s3(filename, resource, content_type)
    job = send_to_zencoder(s3_file)
    return dict(
        zencoder_job_id=job['id'],
        zencoder_outputs=job['outputs'],
    )
