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


Release 0.2.0: *The next big thing®*
====================================

This version uses a database (SQLite, PostgreSQL) for persistence.

- Adds a new CLI option `-s, --skip-merge-commits` to both
  `kwalitee check` commands.  (#60)
- Support for Docker.
- Support for ``.kwalitee.yml`` configuration per repository.
- Cli for preparing release notes ``kwalitee prepare release``.
- Cli for checking changed files ``kwalitee check files``.
- Cli for checking commit messages ``kwalitee check message``.
- Support of ``push`` events.
- Support for multiple repositories.
- Support for multiple users.
- Alembic setup for upcoming migrations.
- New Sphinx documentation.
- Fixes double commenting bug.

Incompatibilities
-----------------

- The commit statuses are still accessible but are not migrated to the
  database.
- Previously created git hooks will have to be uninstalled and
  re-installed as the Flask application is not always created.


Release 0.1.0: *The playground*
===============================

Initial version. It supports ``pull request`` events on one repository and
will perform checks on the commit message and files.

- Commit message checks.
- Git hooks.
- PEP8 checks.
- PEP257 checks.
- PyFlakes checks.
- License checks.
- Asynchronous checks using RQ.
- New unit tests.
- Auto labelling of the pull requests.
- Skip work in progress (wip) pull requests.
