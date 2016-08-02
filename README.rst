==========
 Kwalitee
==========

.. image:: https://img.shields.io/travis/inveniosoftware/kwalitee.svg
        :target: https://travis-ci.org/inveniosoftware/kwalitee

.. image:: https://img.shields.io/coveralls/inveniosoftware/kwalitee.svg
        :target: https://coveralls.io/r/inveniosoftware/kwalitee

.. image:: https://img.shields.io/github/tag/inveniosoftware/kwalitee.svg
        :target: https://github.com/inveniosoftware/kwalitee/releases

.. image:: https://img.shields.io/pypi/dm/kwalitee.svg
        :target: https://pypi.python.org/pypi/kwalitee

.. image:: https://badge.waffle.io/inveniosoftware/kwalitee.svg?label=Status%3A%20ready%20for%20work&title=Issues%20ready%20for%20work
        :target: https://waffle.io/inveniosoftware/kwalitee

.. image:: https://img.shields.io/github/license/inveniosoftware/kwalitee.svg
        :target: https://github.com/inveniosoftware/kwalitee/blob/master/LICENSE

Kwalitee is a tool that runs static analysis checks on Git repository.


* Free software: GPLv2 license
* Documentation: https://pythonhosted.org/kwalitee/

Introduction
============

Kwalitee is a tool that runs static analysis checks on invenio and
invenio-related repositories. It can be used as a web service using the
Github API or as a git hook from the command line.

It aims at slowly, but steadily enforce good practices regarding commit
message formatting, code layout (PEP8), documentation (PYDOCSTYLE) and help
the integrators doing their job without having to worry about recurrent
mistakes.

It relies on and thanks the following softwares and libraries:

 - `pyflakes <https://launchpad.net/pyflakes>`_,
 - `PEP8 <http://legacy.python.org/dev/peps/pep-0008/>`_,
 - `PEP257 <http://legacy.python.org/dev/peps/pep-0257/>`_,

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
