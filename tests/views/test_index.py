# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2014 CERN.
#
# kwalitee is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# kwalitee is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kwalitee; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

from __future__ import unicode_literals

import pytest

from kwalitee.models import Account
from hamcrest import assert_that, equal_to, contains_string


@pytest.fixture(scope="function")
def accounts(session, request):
    names = "invenio", "test", "bob"

    a = []
    for name in names:
        a.append(Account.find_or_create(name))

    def teardown():
        for account in a:
            session.delete(account)
        session.commit()

    request.addfinalizer(teardown)
    return a


def test_simple_status(app, accounts):
    """GET / displays the accounts"""

    tester = app.test_client()
    response = tester.get("/")

    assert_that(response.status_code, equal_to(200))
    body = response.get_data(as_text=True)
    for account in accounts:
        assert_that(body, contains_string(account.name))
