=============================
 Kwalitee v0.2.0 is released
=============================

Kwalitee v0.2.0 was released on February 2, 2015.

About "*The next big thing®*"
-----------------------------

Kwalitee is a tool that runs static analysis checks on invenio and
invenio-related repositories. It can be used as a web service using the
Github API or as a git hook from the command line.

It aims at slowly, but steadily enforce good practices regarding commit
message formatting, code layout (PEP8), documentation (PEP257) and help
the integrators doing their job without having to worry about recurrent
mistakes.

What's new
----------

This version uses a database (SQLite) for persistence.

- Support for Docker. (Jiří)
- Support for ``.kwalitee.yml`` configuration per repository. (Haris)
- Cli for checking changed files ``kwalitee check files``. (Jiří)
- Cli for checking commit messages ``kwalitee check message``. (Jiří)
- Support of ``push`` events. (Yoan)
- Support for multiple repositories. (Yoan)
- Support for multiple users. (Yoan)
- Alembic setup for upcoming migrations (Yoan)
- New Sphinx documentation. (Yoan)
- Fixes double commenting bug. (Yoan)

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

Good luck and thanks for choosing kwalitee.

| Invenio Development Team
|   Email: info@invenio-software.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: http://github.com/inveniosoftware
|   URL: http://invenio-software.org
