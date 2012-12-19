"""
Fabric recipes to document gryphon bootstrapping.
"""

import posixpath
import pkg_resources

pkg_resources.require('yg.deploy>=2.1dev')

from fabric.api import run, cd, sudo
from fabric.contrib import files
from fabric.context_managers import hide, settings

from yg.deploy.fabric import aptitude

def install_airportlocker_required_libs():
    "Install system libs required for airportlocker dependencies"
    required_libs = [
            ]
    with aptitude.package_context(required_libs) as packages:
        packages[:] = []

def _get_build_deps():
    "Install system libs required for building airportlocker"
    return ['python-dev']

def airportlocker_build_deps(action="install"):
    assert action in ('install', 'remove'), "install or remove only"
    libs = _get_build_deps()
    with aptitude.package_context(libs, action=action) as packages:
        if packages:
            print("Installed", packages)
            print("After building, you may remove these new dependencies.")
        packages[:] = []
