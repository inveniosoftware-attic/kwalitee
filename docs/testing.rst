.. _testing:

==========
 Testing
==========

Running the tests are as simple as:

.. code-block:: console

    $ python setup.py test

The code coverage can be outputted by passing some arguments to py.test.

.. code-block:: console

    $ python setup.py test -a "tests --cov invenio_kwalitee --cov-config .coveragerc"
    # html report
    $ python setup.py test -a "tests --cov invenio_kwalitee --cov-report html"

Writing tests
=============

The tests are using PyHamcrest_ for its richness and the nice default output
provided. To be consistent, avoid using :py:mod:`unittest` or bare ``assert``.


Mixins
======

Writing tests, there is two **mixins** you have to be aware of before
reinventing them.

:py:class:`~tests.CaptureMixin`
-------------------------------

The capture mixin monkeypatches :py:data:`sys.stdout` and :py:data:`sys.stderr`
so nothing gets printed to the console and you can evaluate what should have
been printed there.

:py:class:`~tests.DatabaseMixin`
--------------------------------

The database mixin creates a temporary (and empty) disposable database.


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
