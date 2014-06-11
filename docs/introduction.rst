==============
 Introduction
==============

Invenio Kwalitee is a tool that runs static analysis checks on invenio and
invenio-related repositories. It can be used as a web service using the Github
API or as a git hook from the command line.

It aims at slowly, but steadily enforce good practices regarding commit message
formatting, code layout (PEP8), documentation (PEP257) and help the integrators
doing their job without having to worry about recurrent mistakes.

It relies on and thanks the following softwares and libraries:

 - `pyflakes <https://launchpad.net/pyflakes>`_,
 - `PEP8 <http://legacy.python.org/dev/peps/pep-0008/>`_,
 - `PEP257 <http://legacy.python.org/dev/peps/pep-0257/>`_,
 - `RQ <http://python-rq.org/>`_,
 - `Flask <http://flask.pocoo.org/>`_,
 - `Requests <http://pyhton-requests.org/>`_ and
 - `SQLAlchemy <http://www.sqlalchemy.org/>`_.
