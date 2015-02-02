..
    This file is part of kwalitee
    Copyright (C) 2014 CERN.

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

This version uses a database (SQLite) for persistence.

    * cli for checking commit messages ``kwalitee check message`` (Jiří)
    * support of ``push`` events (Yoan)
    * multi-repositories (Yoan)
    * multi-users (Yoan)
    * alembic setup for upcoming migrations (Yoan)
    * sphinx documentation (Yoan)
    * do not comment twice (Yoan)

Incompatibilities
-----------------

    * the commit statuses are still accessible but are not migrated to
      the database.
    * previously created git hooks will have to be uninstalled and re-installed
      as the Flask application is not always created.


Release 0.1.0: *The playground*
===============================

Initial version. It supports ``pull request`` events on one repository and will
perform checks on the commit message and files.

    * Commit message checks (Jiří)
    * Git hooks (Lars)
    * PEP8 checks (Yoan)
    * PEP257 checks (Yoan)
    * pyFlakes checks (Yoan)
    * license checks (Yoan)
    * asynchronous checks using RQ (Yoan)
    * unit testing (Yoan)
    * auto labelling of the pull requests (Yoan)
    * skip work in progress (wip) pull requests (Yoan)
