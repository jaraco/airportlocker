import sys

import setuptools

py26reqs = ['importlib'] if sys.version_info < (2, 7) else []

with open('README.rst') as readme:
    long_description = readme.read()

setup_params = dict(
    name='airportlocker',
    use_hg_version=dict(increment='0.0.1'),
    author="Eric Larson/Jason R. Coombs/Fernando Gutierrez",
    author_email="dev@YouGov.com",
    url="http://dev.yougov.com/",
    packages=setuptools.find_packages(),
    include_package_data=True,
    long_description=long_description,
    entry_points={
        'eggmonster.applications': [
            'main = airportlocker.control.em_launch:run',
        ],
    },
    install_requires=[
        "yg.process>=1.0.2,<2.0dev",
        'yg.launch>=1.1,<2.0dev',
        'jaraco.util',
        'path.py',
        "pymongo>=2.3",
    ] + py26reqs,
    extras_require=dict(
        # note, if you change the server requirements, you must also update
        #  the requirements.txt (because pip doesn't support extras)
        server=[
            "fab>=2.4,<4.0dev",
            "yg.mongodb>=2.0,<3.0dev",
            "zencoder",
            "boto",
            "rsa"
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
        'mock',
    ],
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
