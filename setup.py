from setuptools import setup, find_packages
from pmxtools import hgtools

version = hgtools.get_tag_version() or 'devel'

def strip_first_dir(pths):
	def gen():
		for p in pths:
			yield p[p.find('/')+1:]
	return list(gen())

setup(
	name='airportlocker',
	version=version,
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
		"eggmonster >= 4.0",
		"fab >= 2.3.3",
		#"pear > 2.0",
		"simplejson",
		#"Pyro == 3.5",
		"pmxtools >= 0.14",
		#"faststore == 0.8",
		"ottoman",
	]
)
