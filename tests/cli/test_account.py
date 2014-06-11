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

from __future__ import print_function, unicode_literals

import sys
from unittest import TestCase
from hamcrest import (assert_that, equal_to, contains_string,
                      string_contains_in_order)

from invenio_kwalitee import db
from invenio_kwalitee.models import (Account, Repository, CommitStatus,
                                     BranchStatus)
from invenio_kwalitee.cli.account import add, remove, list as list_

from .. import DatabaseMixin, CaptureMixin


class AccountCliTest(TestCase, DatabaseMixin, CaptureMixin):

    def setUp(self):
        super(AccountCliTest, self).setUp()
        self.databaseUp()
        self.captureUp()

    def tearDown(self):
        self.captureDown()
        self.databaseDown()
        super(AccountCliTest, self).tearDown()

    def test_add(self):
        add("invenio", "invenio@example.org", "123")
        assert_that(sys.stderr.getvalue(),
                    contains_string("invenio"))
        assert_that(Account.query.filter_by(name="invenio",
                                            email="invenio@example.org",
                                            token="123").count(),
                    equal_to(1))

    def test_add_existing(self):
        add("invenio", "test@example.org", "123")
        add("invenio", "invenio@example.org")
        add("invenio", token="456")
        assert_that(Account.query.filter_by(name="invenio",
                                            email="invenio@example.org",
                                            token="456").count(),
                    equal_to(1))

    def test_remove(self):
        """remove {account} drops everything tied to it"""
        add("invenio")

        acc = Account.query.filter_by(name="invenio").first()
        rep = Repository.find_or_create(acc, "foo")
        commit = CommitStatus(rep, "1", "http://")
        db.session.add(commit)
        db.session.commit()
        bs = BranchStatus(commit, "1", "http://")
        db.session.add(bs)
        db.session.commit()

        remove("invenio")

        assert_that(Account.query.filter_by(name="invenio").count(),
                    equal_to(0))
        assert_that(Repository.query.filter_by(name="foo").count(),
                    equal_to(0))
        assert_that(CommitStatus.query.filter_by(repository_id=rep.id).count(),
                    equal_to(0))
        assert_that(BranchStatus.query.filter_by(commit_id=commit.id).count(),
                    equal_to(0))

    def test_double_remove(self):
        add("invenio")
        remove("invenio")
        remove("invenio")
        assert_that(Account.query.filter_by(name="invenio").count(),
                    equal_to(0))

    def test_list(self):
        repos = ["a", "bc", "def", "ghijklmop"]
        for i in range(len(repos)):
            add(repos[-i])
        add("test", "test@тест.укр")
        list_()
        assert_that(sys.stdout.getvalue(), string_contains_in_order(*repos))
        assert_that(sys.stdout.getvalue(), contains_string("test@тест.укр"))
