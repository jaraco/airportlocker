from __future__ import unicode_literals

import argparse
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
	parser.add_argument('filename')
	parser.add_argument('url', help="Airportlocker URL")
	parser.add_argument('-j', '--json', dest='meta', type=json_read_file,
		help='A JSON metadata file', default={}, action=UpdateDict)
	parser.add_argument('-s', '--json-string', dest='meta', type=json_string,
		help='JSON dict string for meta data.', action=UpdateDict)
	parser.add_argument('-n', '--name', action=AddMetadata,
		help='The explicit name you want for the file.')

	return parser.parse_args(*args, **kwargs)

def main():
	args = get_args()

	client = AirportLockerClient(args.url)
	result = client.create(args.filename, args.meta)
	pprint(result)
	pprint(client.view(result['value']))

if __name__ == '__main__':
	main()
