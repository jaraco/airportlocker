from __future__ import unicode_literals

import os
import argparse
import glob
from pprint import pprint

from airportlocker.lib.client import AirportLockerClient
from airportlocker import json

def json_read_file(filename):
    with open(filename) as f:
        return json.load(f)

def json_string(string):
    return json.loads(string)

class AddMetadata(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        namespace.meta[self.dest] = values

class UpdateDict(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        getattr(namespace, self.dest).update(values)

def get_args(*args, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=glob.glob)
    parser.add_argument('url', help="Airportlocker URL")
    parser.add_argument('qx_name', help="questionnaire name")
    return parser.parse_args(*args, **kwargs)

def create_meta(filename, args):
    return dict(
        name=os.path.basename(filename),
        survey=args.qx_name,
        _prefix=args.qx_name,
    )

def main():
    args = get_args()

    client = AirportLockerClient(args.url)
    for filename in args.files:
        result = client.create(filename, create_meta(filename, args))
        print("Added", filename)
        print client.view(unicode(result['value']))

if __name__ == '__main__':
    main()
