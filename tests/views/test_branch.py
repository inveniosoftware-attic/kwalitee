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

"""Integration tests for the branch status page."""

from __future__ import unicode_literals

from hamcrest import assert_that, equal_to, contains_string


def test_get_pull_request(app, owner, repository, commits, branch):
    """GET /{account}/{repository}/branches/{sha}/{branch}."""

    tester = app.test_client()
    response = tester.get("/{0}/{1}/branches/{2}/{3}".format(
                          owner.name,
                          repository.name,
                          commits[-1].sha,
                          branch.name))

    assert_that(response.status_code, equal_to(200))
    body = response.get_data(as_text=True)
    assert_that(body,
                contains_string("/{0}/{1}/".format(
                                owner.name,
                                repository.name)))

    for commit in commits:
        assert_that(body,
                    contains_string("/commits/{0}/".format(commit.sha)))
    assert_that(body, contains_string("Everything is OK."))


def test_get_pull_request_sha_doesnt_exist(app, branch):
    """GET /{account}/{repository}/branches/404/{branch} raise 404."""

    tester = app.test_client()
    response = tester.get("/invenio/test/branches/0000000/{0}".format(
                          branch.name))

    assert_that(response.status_code, equal_to(404))


def test_get_pull_request_doesnt_exist(app, commits):
    """GET /{account}/{repository}/branches/{sha}/404 raise 404."""

    tester = app.test_client()
    response = tester.get("/invenio/test/branches/{0}/404".format(
                          commits[0].sha))

    assert_that(response.status_code, equal_to(404))
