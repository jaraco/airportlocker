import shutil

from paver.easy import task, sh

@task
def build():
    """
    Velociraptor build step
    """
    # when velociraptor runs pip, it installs '.', but the package
    # 'airportlocker' is still here, and causes warnings on startup, so
    # remove it.
    shutil.rmtree('airportlocker')
    sh('dependency-tree --python env/bin/python airportlocker > '
        '"dependency tree.txt"')
