import sys

import setuptools

py26reqs = ['importlib'] if sys.version_info < (2, 7) else []

with open('README.rst') as readme:
    long_description = readme.read()
with open('CHANGES.rst') as changes:
    long_description += '\n\n' + changes.read()

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
        "yg.process==1.0.3",
        'yg.launch==1.1',
        'yg.performance==2.3',
        'jaraco.util',
        'path.py==3.1',
        "pymongo==2.5.2",
    ] + py26reqs,
    extras_require=dict(
        # note, if you change the server requirements, you must also update
        #  the requirements.txt (because pip doesn't support extras)
        server=[
            "fab==3.3",
            "yg.mongodb==2.8",
            "boto==2.19.0",
            "zencoder==0.5",
            "rsa==3.1.1yg3",
            "jaraco.compat==1.1",
        ],
        client=[
            "requests>=1.2",
        ],
    ),
    setup_requires = [
        'hgtools',
        'pytest-runner',
        'jaraco.packaging',
    ],
    tests_require = [
        'pytest',
        'mock',
    ],
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
