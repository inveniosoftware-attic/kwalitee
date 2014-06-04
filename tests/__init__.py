# -*- coding: utf-8 -*-
##
## This file is part of Invenio-Kwalitee
## Copyright (C) 2014 CERN.
##
## Invenio-Kwalitee is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio-Kwalitee is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio-Kwalitee; if not, write to the Free Software Foundation,
## Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
##
## In applying this licence, CERN does not waive the privileges and immunities
## granted to it by virtue of its status as an Intergovernmental Organization
## or submit itself to any jurisdiction.

"""Mocks and mixins for the tests."""

from __future__ import unicode_literals

import os
import sys
import tempfile

from io import StringIO
from invenio_kwalitee import app, db


class MyQueue(object):

    """Queue mock to use in place of the RQ queue.

    .. seealso:: `RQ <http://python-rq.org/docs/>`_
    """

    def __init__(self):
        """Initialize  an empty queue."""
        self.queue = []

    def __len__(self):
        """Length of the queue."""
        return len(self.queue)

    def dequeue(self):
        """Remove one item from the queue."""
        return self.queue.pop()

    def enqueue(self, *args, **kwargs):
        """Add items to the queue.

        :param args: tuple is appended to list
        :param kwargs: are ignored.
        """
        self.queue.append(args)


class DatabaseMixin(object):

    """Mixin to work with a disposable database."""

    in_memory = False
    """Flag to use a real file or in memory database."""

    def databaseUp(self):
        """Set up the database and tables."""
        self.__database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"

        if not self.in_memory:
            fp, self.database = tempfile.mkstemp(".db")
            os.close(fp)

            app.config["SQLALCHEMY_DATABASE_URI"] += "/" + self.database
        else:
            self.database = ":memory:"

        db.create_all()

    def databaseDown(self):
        """Tear down the tables and database."""
        db.session.remove()
        db.drop_all()

        if not self.in_memory:
            os.unlink(self.database)

        app.config["SQLALCHEMY_DATABASE_URI"] = self.__database_uri


class CaptureMixin(object):

    """
    Mixin to capture things from stderr/stdout in tests.

    How to activate it?

    .. code-block:: python

        def setUp(self):
            self.captureUp()
            # identical to
            self.stdoutUp()
            self.stderrUp()

        def tearDown(self):
            self.captureDown()
            # identical to
            self.stdoutDown()
            self.stderrDown()

    How to print (for real)?

    .. code-block:: python

        print(..., file=self._stdout)


    How to read the content from stdout/stderr?

    .. code-block:: python

        sys.stdout.getvalue()
        sys.stderr.getvalue()

    """

    def captureUp(self):
        """Activate the capturing of stderr and stdout."""
        self.stdoutUp()
        self.stderrUp()

    def captureDown(self):
        """Deactivate the capturing of stderr and stdout."""
        self.stdoutDown()
        self.stderrDown()

    def stdoutUp(self):
        """Activate the capturing of stdout."""
        self._stdout = sys.stdout
        sys.stdout = StringIO()

    def stderrUp(self):
        """Activate the capturing of stderr."""
        self._stderr = sys.stderr
        sys.stderr = StringIO()

    def stdoutDown(self):
        """Deactivate the capturing of stdout."""
        sys.stdout = self._stdout

    def stderrDown(self):
        """Deactivate the capturing of stderr."""
        sys.stderr = self._stderr
