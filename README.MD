Easy API for Yandex.Disk
========================

Easy API for Yandex.Disk (http://disk.yandex.ru/)

Features
--------

* Basic authentication
* Creating directories, removing directories and files
* Uploading and downloading files
* Directory listing
* Publishing and UnPublishing

Installation
------------

Install using distribute:

    python setup.py install


Quick Start
-----------

    import eyadisk
    # Start off by creating a client object. Username and
    # password may be omitted if no authentication is needed.
    user = 'username'
    pwd = 'password'

    api = eyadisk.EYaDisk(user=user, pwd=pwd)
    # Do some stuff:
    api.mkdir('eyadisk')
    api.upload('README.MD', '/eyadisk/README.MD')
    url = api.publish('/eyadisk/README.MD')
    print url
    api.download('/eyadisk/README.MD', 'test.md')


Client object API
-----------------

The API is pretty much self-explanatory:

    ls(path)
    mkdir(path)
    mkdirs(path)
    download(remote_file, local_file)
    upload(local_file, remote_file)
    delete(path)
    publish(path)
    unpublish(path)
