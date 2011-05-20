import sys
from setuptools import setup, find_packages

json_req = ['simplejson'] if sys.version < (2,6) else []

setup_params = dict(
	name='airportlocker',
	use_hg_version=dict(increment='0.1'),
	author="Eric Larson/Jason R. Coombs",
	packages=find_packages(),
	include_package_data=True,
	data_files=[
		('', ['unittest.yaml']),
	],
	entry_points={
		'eggmonster.applications' : [
			'main = airportlocker.control.root:run_airportlocker',
			'embed = airportlocker.control.root:start_airportlocker',
		],
	},
	install_requires=[
		"eggmonster>=4.1,<5.0dev",
		"pmxtools>=0.15.36,<1.0dev",
	] + json_req,
	extras_require=dict(
		server=[
			"fab>=2.4,<2.5dev",
			"pymongo",
		],
		client=[
			"httplib2",
		],
	),
	setup_requires = [
		'hgtools',
	],
)

if __name__ == '__main__':
	setup(**setup_params)
