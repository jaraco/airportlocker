import simplejson

from pprint import pprint
from optparse import OptionParser

from airportlocker.lib.client import AirportLockerClient


if __name__ == '__main__':
	usage = 'usage: %prog [OPTIONS] FILENAME LOCKER_URL'
	parser = OptionParser(usage=usage)
	parser.add_option('-j', '--json', dest='jsonfile',
					  help='A JSON metadata file')
	parser.add_option('-s', '--json-string', dest='jsonstr',
					  help='JSON dict string for meta data.')
	parser.add_option('-n', '--name', dest='name',
					  help='The explicit name you want for the file.')

	(options, args) = parser.parse_args()
	if len(args) < 2:
		parser.error('''You must provide the path of a file to upload 
		               and the URL of the airportlocker service.''')
	fields = {}
	if options.name:
		fields.update({'name': options.name})

	if options.jsonfile or options.jsonstr:
		if options.jsonfile:
			try:
				fields.update(simplejson.load(options.jsonfile))
			except:
				parser.error('Failure loading the JSON file.')
				raise
		if options.jsonstr:
			try:
				fields.update(simplejson.loads(options.jsonstr))
			except:
				parser.error('Failure loading the JSON string.')
				raise
	fn, url = args[0], args[1]
	print fn, url
	client = AirportLockerClient(url)
	result = client.create(fn, fields)
	pprint(result)
	pprint(client.view(result['value']))
