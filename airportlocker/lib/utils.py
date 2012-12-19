from __future__ import with_statement

import os

import mimetypes
import tempfile


class MultiPartBody(object):
    def __init__(self, gen):
        self.tempfile = tempfile.TemporaryFile()
        for l in gen():
            self.tempfile.write(l)

    def write(self, txt):
        self.tempfile.write(txt)

    def get(self):
        self.tempfile.seek(0)
        return self.tempfile.read()

    def size(self):
        self.tempfile.seek(0)
        return sum([len(l) for l in self.tempfile])


class MultiPart(object):
    """
    A MIME multipart object for uploading a single _lockerfile
    """
    boundary = '----------12308129817491874--'
    le = '\r\n'
    cd = 'Content-Disposition: form-data;'
    field_header = ' '.join([cd, 'name="%s";'])
    file_header = ' '.join([cd, 'name="%s"; filename="%s"'])
    lbreak = ''

    def __init__(self, fn, fields=None):
        """
        fn is the path to the file on the local filesystem
        """
        self.fn = fn
        self.fields = fields or {}
        self.filename_key = '_lockerfile'
        self._body = MultiPartBody(self._get_body)
        self.content_length = self._body.size()
        self.headers = self._get_headers()

    @property
    def body(self):
        return self._body.get()

    def _start(self):
        return '--%s' % self.boundary

    def _end(self):
        return '--%s--' % self.boundary

    def _content_type(self):
        return 'Content-Type: %s' % (mimetypes.guess_type(self.fn)[0])

    def _get_headers(self):
        return {
            'Content-Type': 'multipart/form-data; boundary=%s' % self.boundary,
            'Content-Length': str(self.content_length),
        }

    def _line(self, line):
        return line + self.le

    def _get_body(self):
        for k, v in self.fields.items():
            yield self._line(self._start())
            yield self._line(self.field_header % k)
            yield self._line(self.lbreak)
            yield self._line(v)
        with open(self.fn, 'r') as fh:
            # browsers normally just pass the filename and not the local path
            # so do the same here.
            filename = os.path.basename(self.fn)
            yield self._line(self._start())
            yield self._line(self.file_header % (self.filename_key, filename))
            yield self._line(self._content_type())
            yield self._line(self.lbreak)
            yield self._line(fh.read())
        yield self._line(self._end())
        yield self._line(self.lbreak)
