import importlib
import rfc822
import time
from unittest import mock
from urlparse import urljoin

import fab
import cherrypy
import pytest
import pkg_resources
import requests

from airportlocker.lib import storage
from airportlocker.lib.test import AirportlockerTest

main = None


def setup_module(mod):
    # we can't import main until the fab base is set :(
    fab.config['base'] = pkg_resources.resource_filename('airportlocker', '')
    mod.main = importlib.import_module('airportlocker.control.main')


class TestReadResource(AirportlockerTest):

    def test_no_args_returns_404(self):
        res = main.ReadResource()
        with pytest.raises(cherrypy.NotFound):
            res.GET(None)

    def test_not_found_returns_404(self):
        """
        If the get_resource function raises a storage.NotFoundError, the GET
        should raise cherrypy.NotFound.
        """
        res = main.ReadResource()
        never_found = mock.Mock(side_effect=storage.NotFoundError)
        res.get_resource = never_found
        with pytest.raises(cherrypy.NotFound):
            res.GET(None, 'foo', 'bar')

    def test_last_modified_header(self, internal_file):
        url = urljoin(self.base_url, 'static/{}'.format(self.test_filename))
        resp = requests.get(url)
        resp.raise_for_status()
        last_modified = resp.headers.get('Last-Modified')
        assert last_modified is not None

        got = time.mktime(rfc822.parsedate(last_modified))
        expected = time.mktime(internal_file.upload_date.timetuple())
        assert got == expected


class TestGetResource(AirportlockerTest):

    def build_resource_url(self, file):
        uri = '/{file.class}/{file.md5}/{file._id}.txt'.format(file=file)
        return urljoin(self.base_url, uri)

    def test_last_modified_header(self, internal_file):
        resp = requests.get(self.build_resource_url(internal_file))
        resp.raise_for_status()
        last_modified = resp.headers.get('Last-Modified')
        assert last_modified is not None

        got = time.mktime(rfc822.parsedate(last_modified))
        expected = time.mktime(internal_file.upload_date.timetuple())
        assert got == expected
