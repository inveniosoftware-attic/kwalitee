..  This file is part of Invenio-Kwalitee
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

.. _testing:

==========
 Testing
==========

Running the tests are as simple as:

.. code-block:: console

    $ python setup.py test

The code coverage can be output by passing some arguments to `py.test
<http://pytest.org/latest/>`_.

.. code-block:: console

    $ python setup.py test -a "tests --cov invenio_kwalitee --cov-config .coveragerc"
    # html report
    $ python setup.py test -a "tests --cov invenio_kwalitee --cov-report html"

Ditto for running only one test or debugging with pdb.

.. code-block:: console

    $ python setup.py test -a tests/tests_ping.py
    $ python setup.py test -a tests/tests_ping.py::test_ping
    $ python setup.py test -a "tests --pdb"


Writing tests
=============

The tests are using PyHamcrest_ for its richness and the nice default output
provided. To be consistent, avoid using :py:mod:`unittest` or bare ``assert``.


Fixtures
========

Fixtures are provided by the very powerful py.test. Take a look at the fixtures
defined in the :ref:`conftest.py <conftest>` files.

Other tools
===========

`HTTPretty <http://falcao.it/HTTPretty/>`_
------------------------------------------

``HTTPretty`` is a HTTP client mock library which lets you define your own
custom answers and status code as well as testing which calls have been made.

:py:mod:`mock`
--------------

``mock`` is used to mock file opening (:py:func:`open`) and inspect the content
that was written in it without having to create temporary files with
:py:mod:`tempfile`.


.. _PyHamcrest: http://pythonhosted.org//PyHamcrest/
