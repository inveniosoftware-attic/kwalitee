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
from invenio_kwalitee import app, db
from invenio_kwalitee.models import (Account, Repository, CommitStatus,
                                     BranchStatus)
from hamcrest import assert_that, equal_to, contains_string

from .. import DatabaseMixin


class BranchesTest(TestCase, DatabaseMixin):

    """Integration tests for the branch page."""

    commits = [
        {"sha": "ef01234"},
        {"sha": "789abcd"},
        {"sha": "0123456"},
    ]
    branch = "spam:wip/my-branch"
    url_template = "https://github.com/invenio/test/commits/{sha}"

    def setUp(self):
        super(BranchesTest, self).setUp()
        self.databaseUp()
        self.owner = Account.find_or_create("invenio")
        self.repository = Repository.find_or_create(self.owner, "test")
        commits = []
        for commit in self.commits:
            cs = CommitStatus(self.repository,
                              commit["sha"],
                              self.url_template.format(**commit))
            commits.append(cs)
            db.session.add(cs)
            db.session.commit()

            # FIXME commits ordering!?
            bs = BranchStatus(commits[-1],
                              self.branch,
                              "http://github.com/pulls/1",
                              {"commits": commits, "files": {}})
            db.session.add(bs)
            db.session.commit()

    def tearDown(self):
        self.databaseDown()
        super(BranchesTest, self).tearDown()

    def test_get_branch(self):
        """GET /{account}/{repository} displays the recent commits."""

        tester = app.test_client(self)
        response = tester.get("/{0}/{1}/branches/{2}".format(
                              self.owner.name,
                              self.repository.name,
                              self.branch))

        assert_that(response.status_code, equal_to(200))
        body = response.get_data(as_text=True)
        assert_that(body,
                    contains_string("/{0}/{1}/".format(
                                    self.owner.name,
                                    self.repository.name)))

        for commit in self.commits:
            assert_that(body,
                        contains_string("/{0}/{1}/branches/{2}/{3}"
                                        .format(self.owner.name,
                                                self.repository.name,
                                                commit["sha"],
                                                self.branch)))
        assert_that(body, contains_string("Everything is OK."))

    def test_get_branch_doesnt_exist(self):
        """GET /{account}/{repository}/branches/404 raise 404 if not found."""

        tester = app.test_client(self)
        response = tester.get("/{0}/{1}/branches/404".format(
                              self.owner.name,
                              self.repository.name))

        assert_that(response.status_code, equal_to(404))
