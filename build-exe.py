"""
Build script to create an uploader as a Windows executable.
"""

import os
import textwrap
import importlib

import setuptools

script_name = 'upload.py'

setup_params = dict(
        console=[script_name],
        script_args=('py2exe',),
        py2exe = dict(
                packages = ['pkg_resources'],
        ),
)

def run():
        importlib.import_module('py2exe')
        open(script_name, 'w').write(textwrap.dedent(
                """
                import airportlocker.lib.upload
                airportlocker.lib.upload.main()
                """))
        setuptools.setup(**setup_params)
        os.remove(script_name)

if __name__ == '__main__':
        run()
