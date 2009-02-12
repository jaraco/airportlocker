from setuptools import setup, find_packages
from pmxtools import hgtools

# version = hgtools.get_tag_version() or 'devel'

def strip_first_dir(pths):
	def gen():
		for p in pths:
			yield p[p.find('/')+1:]
	return list(gen())

setup(
	name='airportlocker',
	version='0.6.1',
	author="Eric Larson",
	packages=find_packages('.'),	  
	package_dir={'airportlocker': 'airportlocker'},
	package_data={
		'airportlocker' : (
			strip_first_dir(hgtools.checked_in('airportlocker/view')) +
			strip_first_dir(hgtools.checked_in('airportlocker/static')) +
			strip_first_dir(hgtools.checked_in('airportlocker/data')) +
			['etc/baseconf.yaml']
		),
	},
	entry_points={
		'eggmonster.applications' : [
			'main = airportlocker.control.root:run_airportlocker',
		],
	},
	install_requires=[
		"eggmonster",
		"fab >= 2.3.3",
		"simplejson",
		"pmxtools >= 0.14",
		"ottoman >= 0.3.1",
	]
)
