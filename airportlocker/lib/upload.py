import argparse
from pprint import pprint

from airportlocker.lib.client import AirportLockerClient
from airportlocker import json

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('filename')
	parser.add_argument('url', help="Airportlocker URL")
	parser.add_argument('-j', '--json', dest='jsonfile',
		help='A JSON metadata file')
	parser.add_argument('-s', '--json-string', dest='jsonstr',
		help='JSON dict string for meta data.')
	parser.add_argument('-n', '--name',
		help='The explicit name you want for the file.')

	args = parser.parse_args()

	fields = {}
	if args.name:
		fields.update({'name': args.name})

	if args.jsonfile or args.jsonstr:
		if args.jsonfile:
			try:
				fields.update(json.load(args.jsonfile))
			except:
				parser.error('Failure loading the JSON file.')
				raise
		if args.jsonstr:
			try:
				fields.update(json.loads(args.jsonstr))
			except:
				parser.error('Failure loading the JSON string.')
				raise
	client = AirportLockerClient(args.url)
	result = client.create(args.filename, fields)
	pprint(result)
	pprint(client.view(result['value']))
