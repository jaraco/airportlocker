import sys

import setuptools

py25reqs = ['simplejson'] if sys.version_info < (2, 6) else []
py26reqs = ['importlib'] if sys.version_info < (2, 7) else []

setup_params = dict(
	name='airportlocker',
	use_hg_version=dict(increment='0.0.1'),
	author="Eric Larson/Jason R. Coombs",
	author_email="Eric.Larson@YouGov.com",
	url="http://dev.yougov.com/",
	packages=setuptools.find_packages(),
	include_package_data=True,
	data_files=[
		('', ['unittest.yaml']),
	],
	entry_points={
		'eggmonster.applications': [
			'main = airportlocker.control.root:run_airportlocker',
			'embed = airportlocker.control.root:start_airportlocker',
		],
	},
	install_requires=[
		"yg.performance>=1.1,<2.0dev",
		"yg.process>=1.0.1,<2.0dev",
	] + py25reqs + py26reqs,
	extras_require=dict(
		server=[
			"eggmonster>=4.1,<6.0dev",
			"fab>=2.4,<3.0dev",
			"pymongo",
		],
		client=[
			"httplib2",
		],
	),
	setup_requires = [
		'hgtools',
		'pytest-runner',
	],
	tests_require = [
		'pytest',
	],
)

if __name__ == '__main__':
	setuptools.setup(**setup_params)
