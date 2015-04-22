import sys, os
import httplib
import base64
import xml.etree.cElementTree as xml
import BaseHTTPServer
from cStringIO import StringIO
from collections import namedtuple

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
        resp = self.request('PROPFIND', '/%s' % folder)
        resp_data = xml.parse(StringIO(resp['data']))
        return [self.elem2file(elem) for elem in resp_data.findall('{DAV:}response')]

    # download file from server
    def download(self, remote_file, local_file):
        self._set_headers('download')
        resp = self.request('GET', '/%s' % remote_file)
        with open(local_file, 'wb') as f:
            f.write(resp['data'])

    # upload file to server
    def upload(self, local_file, remote_file):
        f = open(local_file, 'rb')
        data = f.read()
        self._set_headers('upload', len(data))
        resp = self.request('PUT', remote_file, data)
        f.close()

    # delete file or directory on  server
    def delete(self, file):
        self._set_headers('common')
        resp = self.request('DELETE', '/%s' % file)

    # publish file
    def publish(self, path):
        self._set_headers('common')
        resp = self.request('POST', '/%s' % path + '?publish')
        if resp['status'] != 302:
            raise Exception('Wtf?')
        location = ''
        for key, v in resp['headers']:
            if key == 'location':
                location = v
                break
        return location



    # unpublish file
    def unpublish(self, path):
        self._set_headers('common')
        resp = self.request('POST', '/%s' % path + '?unpublish')

    # create directory on  server
    def mkdir(self, folder):
        self._set_headers('common')
        resp = self.request('MKCOL', '/%s' % folder)

    # create dirs on server (aka mkdir -p)
    def mkdirs(self, path):
        dirs = path.strip('/').split('/')
        path = ''
        for i in range(len(dirs)):
            path = path + '/' + dirs[i]
            self.mkdir_dir(path)

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
        status = response.status
        data = response.read()
        headers = response.getheaders()
        conn.close()
        return {'status':status, 'data':data, 'headers':headers }
