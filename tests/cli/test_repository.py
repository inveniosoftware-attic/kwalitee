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

import sys
from unittest import TestCase
from hamcrest import (assert_that, equal_to, contains_string,
                      string_contains_in_order)
from invenio_kwalitee.models import Account, Repository
from invenio_kwalitee.cli.repository import add, remove, list as list_

from .. import DatabaseMixin, CaptureMixin


class RepositoryCliTest(TestCase, DatabaseMixin, CaptureMixin):

    def setUp(self):
        super(RepositoryCliTest, self).setUp()
        self.databaseUp()
        self.captureUp()

    def tearDown(self):
        self.captureUp()
        self.databaseDown()
        super(RepositoryCliTest, self).tearDown()

    def test_add(self):
        add("invenio/kwalitee")
        assert_that(sys.stderr.getvalue(),
                    contains_string("invenio/kwalitee"))
        assert_that(Account.query.filter_by(name="invenio").count(),
                    equal_to(1))
        assert_that(Repository.query.filter_by(name="kwalitee").count(),
                    equal_to(1))

    def test_add_existing(self):
        add("invenio/kwalitee")
        add("invenio/kwalitee")
        assert_that(Account.query.filter_by(name="invenio").count(),
                    equal_to(1))
        assert_that(Repository.query.filter_by(name="kwalitee").count(),
                    equal_to(1))

    def test_add_invalid_name(self):
        assert_that(add("foo"), equal_to(1))
        assert_that(sys.stderr.getvalue(),
                    contains_string("foo is not a valid repository"))

    def test_remove(self):
        add("invenio/kwalitee")
        remove("invenio/kwalitee")
        remove("invenio/kwalitee")
        remove("kwalitee/kwalitee")
        assert_that(Account.query.filter_by(name="invenio").count(),
                    equal_to(1))
        assert_that(Repository.query.filter_by(name="kwalitee").count(),
                    equal_to(0))

    def test_remove_invalid_name(self):
        assert_that(remove("foo"), equal_to(1))
        assert_that(sys.stderr.getvalue(),
                    contains_string("foo is not a valid repository"))

    def test_list(self):
        repos = ["a/a", "bcd/def", "foo-bar/spam-and-eggs", "foo-bar/zoo"]
        for i in range(len(repos)):
            add(repos[-i])
        list_()
        assert_that(sys.stdout.getvalue(), string_contains_in_order(*repos))
