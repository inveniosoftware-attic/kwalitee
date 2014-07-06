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

"""Configuration for py.test."""

from __future__ import unicode_literals

import os
import sys
import pytest
import tempfile

from io import StringIO
from invenio_kwalitee import create_app
from invenio_kwalitee.models import db as _db, Account, Repository

@pytest.fixture(scope="session")
def app(request):
    """Session-wide test Flask application."""
    config = {
        "TESTING": True,
        "DATABASE_NAME": "testdb"
    }
    app = create_app("invenio_kwalitee", config)

    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope="session")
def db(app, request):
    """Session-wide test database."""
    print(app.config["DATABASE"])
    if os.path.exists(app.config["DATABASE"]):
        os.unlink(app.config["DATABASE"])

    def teardown():
        _db.drop_all()
        print(app.config["DATABASE"])
        os.unlink(app.config["DATABASE"])

    _db.app = app
    _db.create_all()

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope="function")
def session(db, request):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    session = db.create_scoped_session()
    db.session = session

    def teardown():
        transaction.rollback()
        connection.close()
        session.remove()

    request.addfinalizer(teardown)
    return session


@pytest.fixture(scope="function")
def owner(session, request):
    owner = Account.find_or_create("invenio", token="DEADBEEF")

    def teardown():
        session.delete(owner)
        session.commit()

    request.addfinalizer(teardown)
    return owner


@pytest.fixture(scope="function")
def repository(owner, session, request):
    repo = (Repository.find_or_create(owner, "test"))

    def teardown():
        session.delete(repo)
        session.commit()

    request.addfinalizer(teardown)
    return repo

