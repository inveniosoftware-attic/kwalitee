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

"""Integration tests for the branch page."""

from __future__ import unicode_literals

import pytest
from kwalitee.models import CommitStatus, BranchStatus
from hamcrest import assert_that, equal_to, contains_string


@pytest.fixture(scope="function")
def branch(owner, repository, session, request):
    cs = [
        {"sha": "ef01234"},
        {"sha": "789abcd"},
        {"sha": "0123456"},
    ]
    name = "spam:wip/my-branch"
    url_template = "https://github.com/invenio/test/commits/{sha}"

    commits = []
    branches = []
    for commit in cs:
        cs = CommitStatus(repository,
                          commit["sha"],
                          url_template.format(**commit))
        commits.append(cs)
        session.add(cs)
        session.commit()

        bs = BranchStatus(commits[-1],
                          name,
                          "http://github.com/pulls/1",
                          {"commits": commits, "files": {}})
        branches.append(bs)
        session.add(bs)
        session.commit()

    def teardown():
        for bs in branches:
            session.delete(bs)
        session.commit()
        for commit in commits:
            session.delete(commit)
        session.commit()

    request.addfinalizer(teardown)
    return branches[-1]


def test_get_branch(app, owner, repository, branch):
    """GET /{account}/{repository} displays the recent commits."""

    tester = app.test_client()
    response = tester.get("/{0}/{1}/branches/{2}".format(
                          owner.name,
                          repository.name,
                          branch.name))

    assert_that(response.status_code, equal_to(200))
    body = response.get_data(as_text=True)
    assert_that(body,
                contains_string("/{0}/{1}/".format(
                                owner.name,
                                repository.name)))

    for commit in branch.content["commits"]:
        assert_that(body,
                    contains_string("/{0}/{1}/branches/{2}/{3}"
                                    .format(owner.name,
                                            repository.name,
                                            commit,
                                            branch.name)))
    assert_that(body, contains_string("Everything is OK."))


def test_get_branch_doesnt_exist(app, owner, repository):
    """GET /{account}/{repository}/branches/404 raise 404 if not found."""

    tester = app.test_client()
    response = tester.get("/{0}/{1}/branches/404".format(
                          owner.name,
                          repository.name))

    assert_that(response.status_code, equal_to(404))
