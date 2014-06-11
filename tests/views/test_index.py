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

from __future__ import unicode_literals

from unittest import TestCase
from invenio_kwalitee import app
from invenio_kwalitee.models import Account
from hamcrest import assert_that, equal_to, contains_string

from .. import DatabaseMixin


class IndexTest(TestCase, DatabaseMixin):

    """Integration tests for the homepage."""

    accounts = "invenio", "test", "bob"

    def setUp(self):
        super(IndexTest, self).setUp()
        self.databaseUp()
        for account in self.accounts:
            Account.find_or_create(account)

    def tearDown(self):
        self.databaseDown()
        super(IndexTest, self).tearDown()

    def test_simple_status(self):
        """GET / displays the accounts"""

        tester = app.test_client(self)
        response = tester.get("/")

        assert_that(response.status_code, equal_to(200))
        body = response.get_data(as_text=True)
        for account in self.accounts:
            assert_that(body, contains_string(account))
