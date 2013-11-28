#!/usr/bin/env python

import urllib2
import argparse
import json
import time
import itertools

parser = argparse.ArgumentParser()
parser.add_argument('host')
parser.add_argument('port', type=int)
args = parser.parse_args()

root = 'http://{host}:{port}/?surveyName=uptest'.format(**vars(args))
for try_ in itertools.count(1):
    try:
        items = json.load(urllib2.urlopen(root))
        break
    except urllib2.URLError as exc:
        if 'refused' not in unicode(exc).lower() or try_ >= 3:
            raise
        time.sleep(3)
