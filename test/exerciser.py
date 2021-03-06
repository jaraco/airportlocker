import os
import argparse
from pprint import pprint

from six.moves import urllib

import httplib2

from airportlocker.lib.utils import MultiPart
from airportlocker import json

sample_fn = 'sample.txt'

def create_sample_file(name):
    sample_file = os.path.join(os.path.abspath(os.getcwd()), name)
    fh = open(sample_file, 'w+')
    for i in range(0, 10):
        fh.write('%s) hello world\n' % i)
    fh.close()

def update_sample_file(name):
    sample_file = os.path.join(os.path.abspath(os.getcwd()), name)
    fh = open(sample_file, 'w+')
    for i in range(10, 20):
        fh.write('%s) goodbye world\n' % i)
    fh.close()


class AirportLockerClient(object):

    def __init__(self, base):
        self.h = httplib2.Http()
        self.base = base

    def api(self, tail=None):
        return urllib.parse.urljoin(self.base, tail)

    def create(self, fn, fields=None):
        fields = fields or {}
        fields.update({'_new': 'True'})
        data = MultiPart(fn, fields)
        res, c = self.h.request(self.api(),
                                                        method='POST',
                                                        body=data.body,
                                                        headers=data.headers)
        try:
            response = json.loads(c)
        except ValueError:
            pprint(res)
            print(c)
            raise
        return response

    def update(self, id, fn, fields=None):
        fields = fields or {}
        fields.update({'my_extra_data': 'foo'})
        data = MultiPart(fn, fields)
        res, c = self.h.request(self.api('/edit/%s' % id),
                                                        method='PUT',
                                                        body=data.body,
                                                        headers=data.headers)
        try:
            response = json.loads(c)
        except ValueError:
            pprint(res)
            print(c)
            raise
        return response

    def view(self, id):
        res, c = self.h.request(self.api('/view/%s' % id))
        return json.loads(c)

    def read(self, path):
        res, c = self.h.request(self.api('/static/%s' % path))
        return c

    def delete(self, id):
        res, c = self.h.request(self.api('/edit/%s' % id), method='DELETE')
        response = json.loads(c)
        return response

def test_create(exc):
    print('Create')
    create_sample_file(sample_fn)
    sample = exc.create(sample_fn, {'yeah': 'this field'})
    pprint(sample)
    print('Done')
    print()
    return sample['value']

def test_update(exc, id):
    print('Update')
    update_sample_file(sample_fn)
    sample = exerciser.update(id, sample_fn, {'whoa': 'new field', 'yeah': 'updated'})
    pprint(sample)
    print('Done')
    print()

def test_read(exc, id):
    print('Read')
    doc = exc.read(id)
    print(doc)
    print('Done')
    print()


def test_view(exc, id):
    print('View')
    doc = exc.view(id)
    pprint(doc)
    print('Done')
    print()

def test_delete(exc, id):
    print('Delete')
    result = exc.delete(id)
    pprint(result)
    print('Done')
    print()


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()
    exerciser = AirportLockerClient(args.url)
    id = test_create(exerciser)
    test_view(exerciser, id)
    test_read(exerciser, id)
    test_update(exerciser, id)
    test_delete(exerciser, id)


if __name__=='__main__':
    run()
