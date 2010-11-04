from setuptools import setup, find_packages

setup_params = dict(
	name='airportlocker',
	use_hg_version=True,
	author="Eric Larson/Jason R. Coombs",
	packages=find_packages(),	  
	use_package_data=True,
	data_files=[
		('', ['unittest.yaml']),
	],
	entry_points={
		'eggmonster.applications' : [
			'main = airportlocker.control.root:run_airportlocker',
		],
	},
	install_requires=[
		"eggmonster>=4.1,<4.2",
		"fab>=2.3.3,<2.4",
		"pmxtools>=0.15,<0.17dev",
	],
	setup_requires = [
		'hgtools',
	],
)

if __name__ == '__main__':
	setup(**setup_params)
