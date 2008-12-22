from conf import *
import fab
import eggmonster 
from eggmonster import env

fab.config['base'] = BASE

eggmonster.load_default_yaml(file=os.path.join(BASE, 'etc', 'baseconf.yaml'))
if not eggmonster.managed_env():
	eggmonster.load_local_yaml(file=os.path.normpath(os.path.join(BASE, 'devel.yaml')))

from ottoman.client import OttomanServer
fab.register_pool('db', OttomanServer, (env.airportlocker_db_url,))
print 'Regeistered db: ', env.airportlocker_db_url
