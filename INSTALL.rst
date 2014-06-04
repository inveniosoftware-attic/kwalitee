..
    This file is part of Invenio-Kwalitee
    Copyright (C) 2014 CERN.

    Invenio-Kwalitee is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio-Kwalitee is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio-Kwalitee; if not, write to the Free Software Foundation,
    Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

    In applying this licence, CERN does not waive the privileges and immunities
    granted to it by virtue of its status as an Intergovernmental Organization
    or submit itself to any jurisdiction.


Versions
========

We recommend you to use the stable version unless you want to contribute.

Stable version
--------------

Invenio-Kwalitee is on PyPI so all you need is:

.. code-block:: console

    $ pip install --user Invenio-Kwalitee


Development version
-------------------

.. code-block:: console

    $ git clone https://github.com/jirikuncar/invenio-kwalitee
    $ cd invenio-kwalitee
    $ pip install --user -r requirements.txt


Deployment
==========

Invenio-Kwalitee is composed of a WSGI server and a worker to handle the long
tasks asynchronously.

Requirements
------------

- A WSGI web server, we recommend nginx_ + uWSGI_ but anything may do. Apache +
  mod_wsgi_ is working as well.
- A Redis server.

Configuration
-------------

There are not many things you have to configure on a fresh installation, here
are the few you should be aware of.

``ACCESS_TOKEN``
^^^^^^^^^^^^^^^^

Is the API token for your user on Github. You need it in order to be able to
publish comments and statuses.

It can be defined per account as well. See:
:ref:`cli` and :py:class:`invenio_kwalitee.models.Account`.

``AUTO_CREATE``
^^^^^^^^^^^^^^^

Unless ``AUTO_CREATE`` is set to true, you'll have to enable the repositories
individually to authorize events from Github.

.. code-block:: console

    $ kwalitee repository add invenio/test
    invenio/test is now allowed to webhook kwalitee!


WSGI application
----------------

The web application can be served using nginx_ + uWSGI_ or gunicorn_.

Development server
^^^^^^^^^^^^^^^^^^

Using Flask Script's :py:class:`Server <flask_script.Server>`, you can run it
without any external servers or libraries.

.. code-block:: console

    $ kwalitee runserver

uWSGI
^^^^^

This configuration file will serve the applicatino on port ``8000``.

.. code-block:: ini

    ; uwsgi.ini
    [uwsgi]

    http = 0.0.0.0:8000
    master = true

    processes = 4
    die-on-term = true
    vaccum = true
    max-requests = 100

    chdir = <VIRTUALENV>/opt/invenio-kwalitee
    virtualenv = <VIRTUALENV>
    module = invenio_kwalitee.wsgi:application
    touch-reload = uwsgi.ini

    enable-threads = true

And start it this way.

.. code-block:: console

    $ uwsgi --init uwsgi.ini

See more on uWSGI_ documentation.

nginx + uWSGI
^^^^^^^^^^^^^

**TODO**


Worker
------

A simple way to run the worker is the following. It works well for development
and/or debug purposes. Consider relying on a deamon supervisor like: upstart_,
systemd_, runit_ or supervisord_.

.. code-block:: console

    $ python -m invenio_kwalitee.worker

Upstart (Ubuntu)
^^^^^^^^^^^^^^^^

The worker can also be handled using upstart_. Here is the configuration for it.
VirtualEnv_ is a clean way to set everything up and is recommended.

.. code-block:: aconf

    # /etc/init/<myservice>.conf
    description "Kwalitee RQ worker"

    respawn
    respawn limit 15 5
    console log
    setuid <USER>
    setgid <GROUP>

    exec /usr/bin/python -m invenio_kwalitee.worker
    # Or if you've set it up in a virtualenv
    #exec <VIRTUALENV>/bin/python -m invenio_kwalitee.worker

Then, you can manage it using upstart like anything else.

.. code-block:: console

    $ sudo start <myservice>
    $ sudo stop <myservice>


.. _nginx: http://www.nginx.org/
.. _gunicorn: http://gunicorn-docs.readthedocs.org/en/latest/deploy.html
.. _uWSGI: http://uwsgi-docs.readthedocs.org/en/latest/
.. _upstart: http://upstart.ubuntu.com/
.. _systemd: http://freedesktop.org/wiki/Software/systemd/
.. _runit: http://smarden.org/runit/
.. _supervisord: http://supervisord.org/
.. _VirtualEnv: http://virtualenv.readthedocs.org/en/latest/virtualenv.html
.. _mod_wsgi: http://modwsgi.readthedocs.org/en/latest/
