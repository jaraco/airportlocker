import setuptools

with open('README.rst') as readme:
    long_description = readme.read()
with open('CHANGES.rst') as changes:
    long_description += '\n\n' + changes.read()

setup_params = dict(
    name='airportlocker',
    use_scm_version=True,
    author="YouGov, Plc.",
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
        'yg.launch>=2.1,<3.0dev',
        'yg.performance>=1.2.2,<3dev',
        'path.py',
        "six",
    ],
    extras_require=dict(
        # note, if you change the server requirements, you must also update
        #  the requirements.txt (because pip doesn't support extras)
        server=[
            "CherryPy>=3.5,<6dev",
            "routes",
            "yg.mongodb>=4.0,<5dev",
            "boto>=2.7,<3dev",
            "zencoder==0.6.5",
            "rsa",
            "backports.functools_lru_cache",
            "yg.newrelic>=1.2.4",
        ],
        client=[
            "requests>=1.2",
        ],
    ),
    setup_requires=[
        'setuptools_scm',
        'pytest-runner>=2.6.2',
        'jaraco.packaging',
    ],
    tests_require=[
        'pytest',
        'backports.unittest_mock',
    ],
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
