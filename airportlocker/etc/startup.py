from airportlocker.etc.conf import *
import fab
import eggmonster 
from eggmonster import env

fab.config['base'] = BASE

eggmonster.load_default_yaml(file=os.path.join(BASE, 'etc', 'baseconf.yaml'))
if not eggmonster.managed_env():
	eggmonster.load_local_yaml(file=os.path.normpath(os.path.join(BASE, 'devel.yaml')))

from faststore.client import FastStoreClient
fab.register_pool('storage', FastStoreClient, (env.fs_host, env.fs_port),
				  close=lambda c: c.close())
