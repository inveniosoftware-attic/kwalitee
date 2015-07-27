==========
 Kwalitee
==========

.. image:: https://travis-ci.org/inveniosoftware/kwalitee.svg?branch=master
    :target: https://travis-ci.org/inveniosoftware/kwalitee
.. image:: https://coveralls.io/repos/inveniosoftware/kwalitee/badge.svg?branch=master
    :target: https://coveralls.io/r/inveniosoftware/kwalitee


Installation
============

.. seealso:: :ref:`_installation`

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
   * `pyflakes <https://launchpad.net/pyflakes>`_
   * `PEP8 <http://legacy.python.org/dev/peps/pep-0008/>`_
   * `PEP257 <http://legacy.python.org/dev/peps/pep-0257/>`_
   * Copyright year in license

* Commit message analysis:
   * First line less than 50 chars and according to the
     pattern ``<component>: <short description>`` (using nouns).
   * Body with detailed description of what this patch does, formatted as a
     bulletted list. (using present tense).
   * Required signatures: ``Signed-off-by`` and ``Reviewed-by``.


License
=======
Copyright (C) 2014, 2015 CERN.

kwalitee is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

kwalitee is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with kwalitee; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

In applying this licence, CERN does not waive the privileges and immunities granted to it by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.

