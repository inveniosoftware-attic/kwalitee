=================
 Kwalitee v0.2.0
=================

Kwalitee v0.2.0 was released on August 20, 2015.

About "*The next big thing®*"
-----------------------------

Kwalitee is a tool that runs static analysis checks on Git repository. It
can be used as a web service using the Github API or as a git hook from
the command line.

It aims at slowly, but steadily enforce good practices regarding commit
message formatting, code layout (PEP8), documentation (PEP257) and help
the integrators doing their job without having to worry about recurrent
mistakes.

What's new
----------

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

Installation
------------

   $ pip install kwalitee

Documentation
-------------

   http://kwalitee.readthedocs.org/en/v0.2.0

Homepage
--------

   https://github.com/inveniosoftware/kwalitee

Happy hacking and thanks for flying kwalitee.

| Invenio Development Team
|   Email: info@invenio-software.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: http://github.com/inveniosoftware
|   URL: http://invenio-software.org
