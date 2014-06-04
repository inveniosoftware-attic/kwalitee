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


.. _cli:

========================
 Command-line interface
========================

*Invenio-Kwalitee* comes with a command-line tool that goes by the name of
``kwalitee``. If you've installed it using the ``--user`` option, you'll have
to add ``~/.local/bin`` to your path. Otherwise, you should be able to call it
without any trouble.

.. code-block:: console

    $ export PATH+=:~/.local/bin


Help
====

The command line tool is able to give you direct little help.

.. code-block:: console

    $ kwalitee --help

``githooks``
============

This tool can install or uninstall some hooks into the *current* git
repository.

.. seealso::

   * :py:mod:`invenio_kwalitee.cli.githooks`
   * :py:mod:`invenio_kwalitee.hooks`

Hooks
-----

``pre-commit``
^^^^^^^^^^^^^^

Runs the checks on the files about to be commited.

``prepare-commit-msg``
^^^^^^^^^^^^^^^^^^^^^^

Based on the state of the commit create a commit message to be filled in.

.. seealso:: :py:data:`invenio_kwalitee.config.COMMIT_MSG_TEMPLATE`

``post-commit``
^^^^^^^^^^^^^^^

Verifies that the commit message passes the checks.

Installation
------------

.. code-block:: console

    $ kwalitee install

Uninstallation
--------------

.. code-block:: console

    $ kwalitee uninstall

``account``
===========

Utililty to manage to user account that have registred.

Listing
-------

.. code-block:: console

    $ kwalitee account list

Creation and modification
-------------------------

Creation and modification are using the ``add`` command. You can alter the
user's email and its GitHub API token. Any user with a token will have the
comments posted on his repository made using the token's account instead of
the default one.

.. code-block:: console

    $ kwalitee account add <ACCOUNT>

    $ kwalitee account add <ACCOUNT> --email <EMAIL> --token <TOKEN>

.. seealso:: :py:data:`invenio_kwalitee.config.ACCESS_TOKEN`

Deletion
--------

Deletion is permanent and it deletes everything belonging to the given account.

.. code-block:: console

    $ kwalitee account remove <ACCOUNT>


``repository``
==============

Utility to manage to user's repositories.

Listing
-------

.. code-block:: console

    $ kwalitee repository list

Creation
--------

.. code-block:: console

    $ kwalitee repository add <ACCOUNT>/<REPOSITORY>

Deletion
--------

Deletion is permanent and it deletes everything belonging to the given
repository.

.. code-block:: console

    $ kwalitee repository remove <ACCOUNT>/<REPOSITORY>
