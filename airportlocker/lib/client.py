import posixpath
import functools
import os

from six.moves import urllib

from bson import json_util
import requests
from yg.performance import metrics

from airportlocker import json
pjoin = posixpath.join


def RequestsFile(pathname):
    """
    Construct a tuple suitable for a 'file' value per
    http://docs.python-requests.org/en/latest/user/quickstart/#post-a-multipart-encoded-file
    """
    return os.path.basename(pathname), open(pathname, 'rb')


class AirportLockerClient(object):
    _json_params = dict(
        # Use the pymongo object decoder to decode object IDs.
        object_hook=json_util.object_hook,
    )

    def json_result(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs).json(**self._json_params)
        return wrapper

    session = requests.Session()
    # Disable ssl certification validation (#20148)
    session.verify=False

    def __init__(self, url):
        self.base = url
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
        result = urllib.parse.urljoin(base, pjoin(self._api[action], prefix, tail))
        return result

    def new_api(self, filename, survey_name):
        """ New API call, instead of constructing a URL it goes to
        airportlocker, searches for the file and gets the cached md5 url.
        """
        if not filename.startswith('/'):
            filename = '/' + filename

        qs = urllib.parse.urlencode({'filename': filename})
        url = urllib.parse.urljoin(self.base, self.api('signed')) + '?' + qs
        with metrics.Timing('airportlocker.client.request'):
            filejson = self.session.get(url).json(**self._json_params)
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
        return self.session.post(
            self.api('create'),
            data=fields,
            files=dict(
                _lockerfile=RequestsFile(fn),
            ),
        )

    @json_result
    def update(self, id, fn, fields=None):
        fields = fields or {}
        return self.session.put(
            self.api('update', id),
            data=fields,
            files=dict(
                _lockerfile=RequestsFile(fn),
            ),
        )

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
