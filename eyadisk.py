import httplib
import base64
import xml.etree.cElementTree as xml
from cStringIO import StringIO
from collections import namedtuple

class EYaAuth(object):
    """docstring for EYaAuth"""
    def __init__(self, arg):
        super(EYaAuth, self).__init__()
        self.arg = arg

class EYaDisk(object):
    webdav_url = "webdav.yandex.ru"
    File = namedtuple('File', ['name', 'size', 'mtime', 'ctime'])
    headers = {}
    all_headers = {'Accept': '*/*',
        'Authorization': '',
        'Expect': '100-continue',
        'Content-Type': 'application/binary',
        'Depth': 1,
        'Content-Length': 0}

    header_types = {'folder_status': ('Accept',
                                      'Authorization',
                                      'Depth'),
                    'common': ('Accept',
                                      'Authorization'),
                    'download': ('Accept',
                                  'Authorization',
                                  'Content-Type'),
                    'upload': ('Accept',
                                  'Authorization',
                                  'Expect',
                                  'Content-Type',
                                  'Content-Length')}

    def __init__(self, token=None, user=None, pwd=None):
        if token:
            self.auth = 'OAuth %s' % token
        elif user and pwd:
            b_auth = b'%s:%s' % (user, pwd)
            self.auth = 'Basic %s' % base64.b64encode(b_auth)
        else:
            raise Exception()
        self.all_headers['Authorization'] = self.auth

    # list directory on server
    def ls(self, folder):
        self._set_headers('folder_status')
        data = self.request('PROPFIND', '/%s' % folder)
        tree = xml.parse(StringIO(data))
        return [self.elem2file(elem) for elem in tree.findall('{DAV:}response')]

    # download file from server
    def download(self, remote_file, local_file):
        self._set_headers('download')
        data = self.request('GET', '/%s' % remote_file)
        with open(local_file, 'wb') as f:
            f.write(data)

    # upload file to server
    def upload(self, local_file, remote_file):
        f = open(local_file, 'rb')
        data = f.read()
        self._set_headers('upload', len(data))
        self.request('PUT', remote_file, data)
        f.close()

    # delete file or directory on  server
    def delete(self, file):
        self._set_headers('common')
        return self.request('DELETE', '/%s' % file)


    # create directory on  server
    def mkdir(self, folder):
        self._set_headers('common')
        return self.request('MKCOL', '/%s' % folder)

    # create dirs on server (aka mkdir -p)
    def mkdirs(self, path):
        dirs = [d for d in path.split('/') if d]
        if not dirs:
            return
        if path.startswith('/'):
            dirs[0] = '/' + dirs[0]
        old_cwd = self.cwd
        try:
            for dir in dirs:
                self.mkdir(dir)
                self.cd(dir)
        finally:
            self.cd(old_cwd)

    # helper for mkdirs - make path on server
    def cd(self, path):
        path = path.strip()
        if not path:
            return
        stripped_path = '/'.join(part for part in path.split('/') if part) + '/'
        if stripped_path == '/':
            self.cwd = stripped_path
        elif path.startswith('/'):
            self.cwd = '/' + stripped_path
        else:
            self.cwd += stripped_path



    def prop(self, elem, name, default=None):
        child = elem.find('.//{DAV:}' + name)
        return default if child is None else child.text



    def elem2file(self, elem):
        return self.File(
            self.prop(elem, 'href'),
            int(self.prop(elem, 'getcontentlength', 0)),
            self.prop(elem, 'getlastmodified', ''),
            self.prop(elem, 'creationdate', ''),
        )
    # set headers
    def _set_headers(self, header_type, content_len=None):
        self.headers = {}
        for key, val in self.all_headers.items():
            if key in self.header_types[header_type]:
                self.headers[key] = val
        if content_len:
            self.headers['Content-Length'] = content_len

    # send request
    def request(self, method, path, data=None):
        conn = httplib.HTTPSConnection(self.webdav_url)
        conn.putrequest(method, path)
        for key, value in self.headers.items():
            conn.putheader(key, value)
        conn.endheaders()
        if data:
            conn.send(data)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return data;
