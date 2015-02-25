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

"""Integration tests for the commit page."""

from __future__ import unicode_literals

import pytest
from kwalitee.models import CommitStatus
from hamcrest import assert_that, equal_to, contains_string


@pytest.fixture(scope="function")
def commit(repository, session, request):
    sha = "060fcc4e4856b1bc7dc0eba0b07d3c734bbf24fd"
    url_template = "https://github.com/invenio/test/commits/{sha}"

    c = CommitStatus(repository,
                     sha,
                     url_template.format(sha=sha),
                     {"message": ["foo", "bar"],
                      "files": {"spam": {"errors": ["spam"]},
                                "eggs": {"errors": ["eggs"]}}})
    session.add(c)
    session.commit()

    def teardown():
        session.delete(c)
        session.commit()

    request.addfinalizer(teardown)
    return c


def test_get_commit(app, owner, repository, commit):
    """GET /{account}/{repository}/commits/{sha} displays the commit."""

    tester = app.test_client()
    response = tester.get("/{0}/{1}/commits/{2}/".format(
                          owner.name,
                          repository.name,
                          commit.sha))

    assert_that(response.status_code, equal_to(200))
    body = response.get_data(as_text=True)
    assert_that(body,
                contains_string("/{0}/{1}/".format(
                                owner.name,
                                repository.name)))
    assert_that(body,
                contains_string("/commits/{sha}".format(sha=commit.sha)))
    assert_that(body, contains_string("foo"))
    assert_that(body, contains_string("eggs"))


def test_get_commit_doesnt_exist(app):
    """GET /{account}/{repository}/commits/404 raise 404 if not found."""

    tester = app.test_client()
    response = tester.get("/invenio/test/commits/404/")

    assert_that(response.status_code, equal_to(404))
