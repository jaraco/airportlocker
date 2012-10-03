import importlib

import fab
import cherrypy
import py.test
import pkg_resources

main = None

def setup_module(mod):
	# we can't import main until the fab base is set :(
	fab.config['base'] = pkg_resources.resource_filename('airportlocker', '')
	mod.main = importlib.import_module('airportlocker.control.main')

class TestReadResource():
	def test_no_args_returns_404(self):
		res = main.ReadResource()
		with py.test.raises(cherrypy.NotFound):
			res.GET(None)
