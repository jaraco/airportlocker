from __future__ import print_function

import os

from pprint import pformat
from optparse import OptionParser

from airportlocker.lib.client import AirportLockerClient


class GryphonAPLClient(object):

    def __init__(self, base, survey=None):
        self.req = {}
        if survey:
            self.req['_prefix'] = survey
            self.req['survey'] = survey
        self.survey = survey
        self.api = AirportLockerClient(base)
        self.files = []

    def add(self, fname):
        if not os.path.isfile(fname):
            raise IOError('"%s" is not a file or does not exist' % fname)
        self.files.append(fname)

    def upload(self):
        meta = self.req.copy()
        for i, f in enumerate(self.files):
            filename = os.path.basename(f)
            meta['name'] = filename
            meta['title'] = ''
            result = self.api.create(f, meta)
            if result['status'] == 'success':
                print('%s created' % filename)
            else:
                print('Error: %s' % pformat(result))
                print('Skipped:')
                print(' '.join(self.files[i - 1:]))
                break
        print('Done!')

def run():
    usage = 'usage: %prog [-v | --verbose] [-s surveyname] file1 file2 file3 ...'
    parser = OptionParser(usage=usage)
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
        help='Print verbose output')
    parser.add_option('-s', '--survey', dest='survey',
        help='Add files to a specific survey')

    options, args = parser.parse_args()
    if len(args) < 1:
        parser.error('You must provide at least one file to upload')

    base_url = 'https://surveyfiles.yougov.com/'
    client = GryphonAPLClient(base_url, options.survey)
    for fname in args:
        try:
            client.add(fname)
        except IOError, e:
            parser.error(e)
    client.upload()

if __name__ == '__main__':
    run()
