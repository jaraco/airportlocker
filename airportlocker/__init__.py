
# prefer simplejson to json, but fallback to json
try:
	import simplejson as json
except ImportError:
	import json
