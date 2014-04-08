================
Invenio-Kwalitee
================

.. image:: https://travis-ci.org/jirikuncar/invenio-kwalitee.png?branch=master
    :target: https://travis-ci.org/jirikuncar/invenio-kwalitee
.. image:: https://coveralls.io/repos/jirikuncar/invenio-kwalitee/badge.png?branch=master
    :target: https://coveralls.io/r/jirikuncar/invenio-kwalitee

Installation
============
Invenio-Kwalitee is on PyPI so all you need is: ::

    pip install Invenio-Kwalitee

Git Hooks
=========
Install git hooks into your repository using::

    cd /path/to/git-repo
    kwalitee githooks install

and uninstall hooks using::

    kwalitee githooks uninstall

Following hooks are installed:

* ``pre-commit`` - run PEP8, pyflakes and copyright year checks on files
  being committed. If errors are found, the commit is aborted.
* ``prepare-commit-msg`` - prepare standard form commit message.
* ``post-commit`` - check commit message form and signatures. If errors are
  found, they can be fixed with ``git commit --amend``.

All checks can be disabled using::

    git commit --no-verify


Kwalitee checks
===============

* Static analysis of files:
   * pyflake
   * PEP8
   * Copyright year in license

* Commit message analysis:
   * First line less than 50 chars and according to the
     pattern ``<component>: <short description>`` (using nouns).
   * Body with detailed description of what this patch does, formatted as a
     bulletted list. (using present tense).
   * Required signatures: ``Signed-off-by`` and ``Reviewed-by``.

Testing
=======
Running the tests are as simple as: ::

    python setup.py test

or (to also show test coverage) ::

    python setup.py nosetests

Deployment
==========

Upstart (Ubuntu)
----------------

The web application can be served using nginx_ + uWSGI_ or gunicorn_ and the
worker can also be handled using upstart_. Here is the configuration for it.
VirtualEnv_ is a clean way to set everything up and is recommended.::

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

Then, you can manage it using upstart like anything else.::

    $ sudo start <myservice>
    $ sudo stop <myservice>

.. _nginx: http://gunicorn-docs.readthedocs.org/en/latest/deploy.html
.. _uWSGI: http://uwsgi-docs.readthedocs.org/en/latest/Upstart.html
.. _gunicorn: http://gunicorn-docs.readthedocs.org/en/latest/deploy.html#upstart
.. _upstart: http://upstart.ubuntu.com/
.. _VirtualEnv: http://virtualenv.readthedocs.org/en/latest/virtualenv.html

License
=======
Copyright (C) 2014 CERN.

Invenio-Kwalitee is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

Invenio-Kwalitee is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Invenio-Kwalitee; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

In applying this licence, CERN does not waive the privileges and immunities granted to it by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.

