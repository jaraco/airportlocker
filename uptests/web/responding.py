#!/usr/bin/env python

import argparse
import requests
import portend

parser = argparse.ArgumentParser()
parser.add_argument('host')
parser.add_argument('port', type=int)
args = parser.parse_args()
portend.occupied(args.host, args.port, timeout=10)

root = 'http://{host}:{port}/?surveyName=uptest'.format(**vars(args))
status = requests.get(root).json()
assert status, "Empty status received"
