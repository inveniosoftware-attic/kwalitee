..
    This file is part of kwalitee
    Copyright (C) 2014, 2015 CERN.

    kwalitee is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    kwalitee is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with kwalitee; if not, write to the Free Software Foundation,
    Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

    In applying this licence, CERN does not waive the privileges and immunities
    granted to it by virtue of its status as an Intergovernmental Organization
    or submit itself to any jurisdiction.


Versions
========

We recommend you to use the stable version unless you want to contribute.

Stable version
--------------

kwalitee is on PyPI so all you need is:

.. code-block:: console

    $ pip install --user kwalitee


Development version
-------------------

.. code-block:: console

    $ git clone https://github.com/inveniosoftware/kwalitee
    $ cd kwalitee
    $ pip install --user -r requirements.txt


Installation of the command-line interface
==========================================

Kwalitee can be used as a :ref:`cli`, which has some handy features like the
:ref:`githooks` and the :ref:`messages` checks.

By default the messages checks will try to use ``GitPython`` but we are
recommending you to install and use `pygit2 <http://www.pygit2.org/>`_. As, it
has not stable version yet, the installation requires some work.

Ubuntu
------

.. code-block:: console

    $ sudo apt-add-repository ppa:dennis/python
    $ sudo apt-get update
    $ sudo apt-get install python-dev libffi-dev libgit2
    $ pip install cffi pygit2

If you don't find a suitable version using ``ppa:dennis/python``, you can
always install it manually via ``cmake``.

OSX
---

The important detail here is to use the same version for ``libgit2`` **and**
``pygit2``. `Homebrew <http://brew.sh/>`_ is a way to get it working.

.. code-block:: console

    $ brew update
    $ brew install libgit2 # currently 0.21.0 (2014-07-28)
    $ pip install pygit2
