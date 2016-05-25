import email.utils
import time
from unittest import mock

from six.moves.urllib.parse import urljoin

import cherrypy
import pytest
import requests

from airportlocker.lib import storage
from airportlocker.lib.test import AirportlockerTest
from airportlocker.control import main


class TestReadResource(AirportlockerTest):

    def test_no_args_returns_404(self):
        res = main.ReadResource()
        with pytest.raises(cherrypy.NotFound):
            res.GET('')

    def test_not_found_returns_404(self):
        """
        If the get_resource function raises a storage.NotFoundError, the GET
        should raise cherrypy.NotFound.
        """
        res = main.ReadResource()
        never_found = mock.Mock(side_effect=storage.NotFoundError)
        res.get_resource = never_found
        with pytest.raises(cherrypy.NotFound):
            res.GET('foo/bar')

    @property
    def static_url(self):
        return urljoin(self.base_url, 'static/{}'.format(self.test_filename))

    def test_GET_returns_last_modified_header(self, internal_file):
        resp = requests.get(self.static_url)
        resp.raise_for_status()
        last_modified = resp.headers.get('Last-Modified')
        assert last_modified is not None

        got = time.mktime(email.utils.parsedate(last_modified))
        expected = time.mktime(internal_file.upload_date.timetuple())
        assert got == expected

    def test_HEAD_returns_last_modified_header(self, internal_file):
        resp = requests.head(self.static_url)
        resp.raise_for_status()
        last_modified = resp.headers.get('Last-Modified')
        assert last_modified is not None

        got = time.mktime(email.utils.parsedate(last_modified))
        expected = time.mktime(internal_file.upload_date.timetuple())
        assert got == expected


class TestGetResource(AirportlockerTest):

    def build_resource_url(self, file):
        uri = '/{file.class}/{file.md5}/{file._id}.txt'.format(file=file)
        return urljoin(self.base_url, uri)

    def test_GET_returns_last_modified_header(self, internal_file):
        resp = requests.get(self.build_resource_url(internal_file))
        resp.raise_for_status()
        last_modified = resp.headers.get('Last-Modified')
        assert last_modified is not None

        got = time.mktime(email.utils.parsedate(last_modified))
        expected = time.mktime(internal_file.upload_date.timetuple())
        assert got == expected


class TestSignedResources(AirportlockerTest):

    def test_list(self):
        path = '/signed/'
        url = urljoin(self.base_url, path)
        resp = requests.get(url)
        resp.raise_for_status()
        res = resp.json()
        assert isinstance(res, list)

    def test_query(self):
        path = '/signed/?filename=%2FFDRC0017%2FScreenshot_1.jpg'
        url = urljoin(self.base_url, path)
        resp = requests.get(url)
        resp.raise_for_status()
        res = resp.json()
        assert isinstance(res, list)
