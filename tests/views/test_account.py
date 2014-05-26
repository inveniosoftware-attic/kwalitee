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
from invenio_kwalitee.models import Account, Repository
from hamcrest import assert_that, equal_to, contains_string

from .. import DatabaseMixin


class AccountTest(TestCase, DatabaseMixin):

    """Integration tests for the account page."""

    repositories = "invenio", "test", "bob"

    def setUp(self):
        super(AccountTest, self).setUp()
        self.databaseUp()
        self.owner = Account.find_or_create("invenio")
        for repository in self.repositories:
            Repository.find_or_create(self.owner, repository)

    def tearDown(self):
        self.databaseDown()
        super(AccountTest, self).tearDown()

    def test_get_account(self):
        """GET /{account} displays the repositories."""

        tester = app.test_client(self)
        response = tester.get("/{0}/".format(self.owner.name))

        assert_that(response.status_code, equal_to(200))
        for repository in self.repositories:
            assert_that(response.get_data(as_text=True),
                        contains_string("/{0}/{1}/".format(self.owner.name,
                                                           repository)))

    def test_get_account_doesnt_exist(self):
        """GET /{account} raise 404 if not found."""

        tester = app.test_client(self)
        response = tester.get("/404/")

        assert_that(response.status_code, equal_to(404))
