import importlib

import fab
import cherrypy
import py.test
import mock
import pkg_resources

from airportlocker.lib import storage

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

	def test_not_found_returns_404(self):
		"""
		If the get_resource function raises a storage.NotFoundError, the GET
		should raise cherrypy.NotFound.
		"""
		res = main.ReadResource()
		never_found = mock.Mock(side_effect=storage.NotFoundError)
		res.get_resource = never_found
		with py.test.raises(cherrypy.NotFound):
			res.GET(None, 'foo', 'bar')
