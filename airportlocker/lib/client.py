import posixpath
import urllib
import urlparse
import functools

from bson import json_util
import requests

from airportlocker.lib.utils import MultiPart
from airportlocker import json
pjoin = posixpath.join


def build_session():
    session = requests.Session()
    # For #20148 we disable ssl certification validations
    session.verify=False
    return session

def decode_json(result):
    """
    Decode a requests result object using its .json() method. Use
    the pymongo object decoder to decode object IDs.
    """
    return result.json(object_hook=json_util.object_hook)

def json_result(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return decode_json(func(*args, **kwargs))
    return wrapper

class AirportLockerClient(object):

    def __init__(self, url, session=None):
        self.base = url
        self.session = session or build_session()
        self._api = {
            'query': '',
            'create': '',
            'update': '/edit',
            'read': '/static',
            'view': '/view',
            'delete': '/edit',
            'signed': '/signed/',
        }

    def api(self, action, tail=None, prefix=None, use_host=True):
        tail = tail or ''
        prefix = prefix or ''
        base = self.base
        if not use_host:
            base = ''
        result = urlparse.urljoin(base, pjoin(self._api[action], prefix, tail))
        return result

    def new_api(self, filename, survey_name):
        """ New API call, instead of constructing a URL it goes to
        airportlocker, searches for the file and gets the cached md5 url.
        """
        if not filename.startswith('/'):
            filename = '/' + filename

        url = urlparse.urljoin(self.base, self.api('signed')) + '?' + \
              urllib.urlencode({'filename': filename})
        filejson = decode_json(self.session.get(url))
        if not len(filejson) and not filename.startswith('/' + survey_name):
            # Try to find the file with the survey_name as prefix
            return self.new_api('/' + survey_name + filename, survey_name)

        if len(filejson):
            return json.dumps({'found': True, 'meta': filejson[0]})

        return json.dumps({"found": False, "meta": {}})

    @json_result
    def create(self, fn, fields=None):
        fields = fields or {}
        fields.update({'_new': 'True'})
        data = MultiPart(fn, fields)
        return self.session.post(self.api('create'),
                                data=data.body,
                                headers=data.headers)

    @json_result
    def update(self, id, fn, fields=None):
        fields = fields or {}
        data = MultiPart(fn, fields)
        return self.session.put(self.api('update', id),
                                data=data.body,
                                headers=data.headers)

    @json_result
    def view(self, id):
        return self.session.get(self.api('view', id))

    def read(self, path, prefix=''):
        return self.session.get(self.api('read', path)).content

    @json_result
    def delete(self, id):
        return self.session.delete(self.api('delete', id))

    def exists(self, id, prefix=''):
        res = None
        try:
            res = self.session.head(self.api('read', id, prefix=prefix))
        except Exception:
            pass
        return bool(res)

    @json_result
    def query(self, qs):
        qs = '?q=%s' % qs
        return self.session.get(self.api('query', qs))
